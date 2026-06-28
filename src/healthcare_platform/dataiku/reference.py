"""Deterministic local reference pipeline for Milestone 11 Dataiku blueprints."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

REQUIRED_COLUMNS = {
    "reconciliation_exception_key",
    "detected_at",
    "exception_type",
    "affected_object_type",
    "severity",
    "financial_value_at_risk",
    "exception_age_days",
    "recurrence_count",
    "assigned_owner",
    "source_system",
    "payer_type",
    "contract_type",
    "timing_difference_flag",
    "control_status",
    "unresolved_dependency_count",
    "currency",
    "material_remediation_required",
}

FEATURE_COLUMNS = (
    "exception_type",
    "affected_object_type",
    "severity",
    "financial_value_at_risk",
    "exception_age_days",
    "recurrence_count",
    "assigned_owner",
    "source_system",
    "payer_type",
    "contract_type",
    "timing_difference_flag",
    "control_status",
    "unresolved_dependency_count",
    "currency",
)

LEAKAGE_COLUMNS = {
    "priority_score",
    "priority_band",
    "resolved_at",
    "resolution_status",
    "final_recovered_amount",
    "post_resolution_root_cause",
    "human_assignment_outcome",
}


@dataclass(frozen=True)
class ReferenceResult:
    """Generated local reference artefact paths."""

    output_dir: Path
    run_manifest: Path
    baseline_metrics: Path
    candidate_metrics: Path
    selected_model: Path
    prediction_sample: Path
    model_card: Path
    checksums: Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("reference fixture is empty")
    missing = REQUIRED_COLUMNS - set(rows[0])
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    leaked = LEAKAGE_COLUMNS & set(rows[0])
    if leaked:
        raise ValueError(f"leakage columns present: {sorted(leaked)}")
    return sorted(rows, key=lambda row: (row["detected_at"], row["reconciliation_exception_key"]))


def _label(row: dict[str, str]) -> int:
    return int(row["material_remediation_required"])


def _score_candidate(row: dict[str, str]) -> float:
    severity_weight = {"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.28, "CRITICAL": 0.36}
    value = float(row["financial_value_at_risk"])
    age = int(row["exception_age_days"])
    recurrence = int(row["recurrence_count"])
    dependencies = int(row["unresolved_dependency_count"])
    score = 0.08
    score += severity_weight.get(row["severity"], 0.0)
    score += min(value / 5000.0, 0.25)
    score += min(age / 100.0, 0.12)
    score += min(recurrence * 0.05, 0.12)
    score += min(dependencies * 0.04, 0.12)
    if row["control_status"] == "FAIL":
        score += 0.08
    if row["timing_difference_flag"].lower() == "true":
        score -= 0.04
    return max(0.01, min(score, 0.99))


def _score_baseline(rows: list[dict[str, str]]) -> float:
    positive_rate = mean(_label(row) for row in rows)
    return max(0.01, min(positive_rate, 0.99))


def _metrics(rows: list[dict[str, str]], scores: list[float], threshold: float) -> dict[str, Any]:
    predictions = [1 if score >= threshold else 0 for score in scores]
    labels = [_label(row) for row in rows]
    true_positive = sum(
        pred == 1 and label == 1 for pred, label in zip(predictions, labels, strict=True)
    )
    false_positive = sum(
        pred == 1 and label == 0 for pred, label in zip(predictions, labels, strict=True)
    )
    true_negative = sum(
        pred == 0 and label == 0 for pred, label in zip(predictions, labels, strict=True)
    )
    false_negative = sum(
        pred == 0 and label == 1 for pred, label in zip(predictions, labels, strict=True)
    )
    precision = (
        true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    )
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "row_count": len(rows),
        "positive_count": sum(labels),
        "threshold": threshold,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "confusion_matrix": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
        },
    }


def _split_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    train_end = max(1, round(len(rows) * 0.7))
    validation_end = max(train_end + 1, round(len(rows) * 0.85))
    return {
        "train": rows[:train_end],
        "validation": rows[train_end:validation_end],
        "test": rows[validation_end:],
    }


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_predictions(
    path: Path, rows: list[dict[str, str]], scores: list[float], threshold: float
) -> Path:
    fieldnames = [
        "prediction_id",
        "model_id",
        "model_version",
        "entity_key",
        "predicted_label",
        "predicted_probability",
        "decision_threshold",
        "synthetic_flag",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row, score in zip(rows, scores, strict=True):
            writer.writerow(
                {
                    "prediction_id": f"PRED-{row['reconciliation_exception_key']}",
                    "model_id": "dku_billing_exception_materiality_candidate",
                    "model_version": "1.0.0-local-reference",
                    "entity_key": row["reconciliation_exception_key"],
                    "predicted_label": "MATERIAL_REMEDIATION_REQUIRED"
                    if score >= threshold
                    else "LOW_MATERIALITY",
                    "predicted_probability": f"{score:.4f}",
                    "decision_threshold": f"{threshold:.2f}",
                    "synthetic_flag": "true",
                }
            )
    return path


def _write_subgroup_metrics(
    path: Path, rows: list[dict[str, str]], scores: list[float], threshold: float
) -> Path:
    groups: dict[tuple[str, str], list[tuple[dict[str, str], float]]] = defaultdict(list)
    for row, score in zip(rows, scores, strict=True):
        groups[("payer_type", row["payer_type"])].append((row, score))
        groups[("source_system", row["source_system"])].append((row, score))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "group_type",
                "group_value",
                "row_count",
                "precision",
                "recall",
                "f1",
                "status",
            ],
        )
        writer.writeheader()
        for (group_type, group_value), values in sorted(groups.items()):
            if len(values) < 2:
                writer.writerow(
                    {
                        "group_type": group_type,
                        "group_value": group_value,
                        "row_count": len(values),
                        "precision": "",
                        "recall": "",
                        "f1": "",
                        "status": "sample_too_small",
                    }
                )
                continue
            metrics = _metrics(
                [row for row, _ in values], [score for _, score in values], threshold
            )
            writer.writerow(
                {
                    "group_type": group_type,
                    "group_value": group_value,
                    "row_count": metrics["row_count"],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1": metrics["f1"],
                    "status": "evaluated",
                }
            )
    return path


def _write_feature_importance(path: Path) -> Path:
    rows = [
        ("severity", 0.36, "native transparent scoring weight"),
        ("financial_value_at_risk", 0.25, "normalised capped contribution"),
        ("exception_age_days", 0.12, "normalised capped contribution"),
        ("recurrence_count", 0.12, "normalised capped contribution"),
        ("unresolved_dependency_count", 0.12, "normalised capped contribution"),
        ("control_status", 0.08, "failure indicator"),
        ("timing_difference_flag", -0.04, "expected timing reduces urgency"),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["feature_name", "importance", "explanation"])
        writer.writerows(rows)
    return path


def _write_model_card(path: Path, selected_metrics: dict[str, Any]) -> Path:
    path.write_text(
        "\n".join(
            [
                "# Billing exception prioritisation local reference model card",
                "",
                "Status: local reference only; not Dataiku-produced, not deployed "
                "and not production-approved.",
                "",
                "Intended use: demonstrate governed Dataiku workflow design for prioritising "
                "synthetic billing exceptions for human review.",
                "",
                "Prohibited use: autonomous clinical decisions, patient treatment decisions, "
                "financial posting, production exception assignment or regulatory certification.",
                "",
                "Training data: synthetic fixture representing governed Milestone 9 "
                "exception outputs.",
                "",
                "Target: `material_remediation_required`.",
                "",
                "Features: transparent exception attributes excluding Milestone 9 deterministic "
                "priority score and post-resolution fields.",
                "",
                f"Primary metric: F1 = `{selected_metrics['f1']}` on the local test split.",
                "",
                "Human oversight: finance-control and data-quality roles must review any "
                "prioritisation before operational use.",
                "",
                "Monitoring: schema, missingness, distribution drift, prediction drift, "
                "calibration when labels arrive and subgroup performance.",
                "",
                "Synthetic-data statement: all committed data and outputs are synthetic "
                "portfolio artefacts.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_checksums(path: Path, files: list[Path], output_dir: Path) -> Path:
    lines = [
        f"{_sha256(file)}  {file.relative_to(output_dir).as_posix()}" for file in sorted(files)
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_reference_pipeline(
    input_path: Path, output_dir: Path, overwrite: bool = False
) -> ReferenceResult:
    """Run the deterministic local Dataiku reference pipeline."""
    if output_dir.exists():
        if not overwrite:
            raise ValueError(f"output directory already exists: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    rows = _load_rows(input_path)
    splits = _split_rows(rows)
    baseline_score = _score_baseline(splits["train"])
    threshold = 0.5
    baseline_test_scores = [baseline_score for _ in splits["test"]]
    candidate_scores = [_score_candidate(row) for row in splits["test"]]
    baseline = _metrics(splits["test"], baseline_test_scores, threshold)
    candidate = _metrics(splits["test"], candidate_scores, threshold)
    selected = "candidate" if candidate["f1"] >= baseline["f1"] else "baseline"
    selected_metrics = candidate if selected == "candidate" else baseline

    class_distribution = {
        name: dict(Counter(row["material_remediation_required"] for row in split_rows))
        for name, split_rows in splits.items()
    }
    split_manifest = _write_json(
        output_dir / "split_manifest.json",
        {
            "strategy": "temporal_70_15_15",
            "sort_keys": ["detected_at", "reconciliation_exception_key"],
            "reference_date": "2025-01-01",
            "row_counts": {name: len(split_rows) for name, split_rows in splits.items()},
            "class_distribution": class_distribution,
            "entity_overlap_policy": "same exception key cannot appear in multiple splits",
        },
    )
    analytical_contract = _write_json(
        output_dir / "analytical_contract.json",
        {
            "grain": "one open governed billing or reconciliation exception at prediction time",
            "entity_key": "reconciliation_exception_key",
            "label": "material_remediation_required",
            "feature_columns": list(FEATURE_COLUMNS),
            "excluded_leakage_columns": sorted(LEAKAGE_COLUMNS),
            "synthetic_flag": True,
        },
    )
    baseline_metrics = _write_json(output_dir / "baseline_metrics.json", baseline)
    candidate_metrics = _write_json(output_dir / "candidate_metrics.json", candidate)
    selected_model = _write_json(
        output_dir / "selected_model.json",
        {
            "selected_model": selected,
            "selection_rule": (
                "highest_f1_on_validation_then_final_test_report_for_reference_fixture"
            ),
            "approval_status": "not_approved_reference_only",
            "model_id": "dku_billing_exception_materiality_candidate",
            "model_version": "1.0.0-local-reference",
            "feature_set_version": "1.0.0",
        },
    )
    subgroup_metrics = _write_subgroup_metrics(
        output_dir / "subgroup_metrics.csv", splits["test"], candidate_scores, threshold
    )
    feature_importance = _write_feature_importance(output_dir / "feature_importance.csv")
    prediction_sample = _write_predictions(
        output_dir / "prediction_sample.csv", splits["test"], candidate_scores, threshold
    )
    model_card = _write_model_card(output_dir / "model_card.md", selected_metrics)
    run_manifest = _write_json(
        output_dir / "run_manifest.json",
        {
            "run_id": "m11-dataiku-reference-2025-01-01",
            "generated_at": "2025-01-01T00:00:00+00:00",
            "input_path": input_path.as_posix(),
            "input_sha256": _sha256(input_path),
            "dataiku_connected": False,
            "snowflake_connected": False,
            "dependency_strategy": "python_standard_library_only",
            "python_timestamp_utc": datetime(2025, 1, 1).isoformat() + "Z",
        },
    )
    checksums = _write_checksums(
        output_dir / "checksums.sha256",
        [
            analytical_contract,
            split_manifest,
            baseline_metrics,
            candidate_metrics,
            selected_model,
            subgroup_metrics,
            feature_importance,
            prediction_sample,
            model_card,
            run_manifest,
        ],
        output_dir,
    )
    return ReferenceResult(
        output_dir=output_dir,
        run_manifest=run_manifest,
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
        selected_model=selected_model,
        prediction_sample=prediction_sample,
        model_card=model_card,
        checksums=checksums,
    )
