"""Deterministic local reference retrieval for the offline feature store."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

REGISTRY_ROOT = Path("feature_store/registry")
DEFAULT_FIXTURE = Path("feature_store/reference/fixtures/exception_events.csv")
FEATURE_SET_ID = "billing_exception_prioritisation_features"
FEATURE_SET_VERSION = "1.0.0"


@dataclass(frozen=True)
class FeatureStoreReferenceResult:
    """Generated feature-store reference artefacts."""

    output_dir: Path
    retrieval_manifest: Path
    validation_report: Path
    historical_training_set: Path
    batch_scoring_set: Path
    checksums: Path


def _read_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"expected mapping in {path}")
    return loaded


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_events(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "entity_key",
        "observation_timestamp",
        "affected_object_type",
        "source_system",
        "payer_context",
        "event_time",
        "availability_time",
        "severity",
        "financial_value_at_risk",
        "control_status",
    }
    if not rows:
        raise ValueError("feature fixture is empty")
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"missing fixture columns: {sorted(missing)}")
    return rows


def validate_registry(root: Path = REGISTRY_ROOT) -> dict[str, Any]:
    """Validate registry integrity without connecting to external systems."""
    entities = _read_yaml(root / "entities.yaml")["entities"]
    features = _read_yaml(root / "features.yaml")["features"]
    views = _read_yaml(root / "feature_views.yaml")["feature_views"]
    sets = _read_yaml(root / "feature_sets.yaml")["feature_sets"]
    consumers = _read_yaml(root / "consumers.yaml")["consumers"]
    lifecycle = _read_yaml(root / "lifecycle.yaml")
    statuses = set(lifecycle["allowed_statuses"])

    entity_ids = {entity["entity_id"] for entity in entities}
    feature_ids = [feature["feature_id"] for feature in features]
    view_ids = [view["feature_view_id"] for view in views]
    set_ids = [feature_set["feature_set_id"] for feature_set in sets]
    errors: list[str] = []
    if len(feature_ids) != len(set(feature_ids)):
        errors.append("duplicate feature IDs")
    if len(view_ids) != len(set(view_ids)):
        errors.append("duplicate feature view IDs")
    if len(set_ids) != len(set(set_ids)):
        errors.append("duplicate feature set IDs")
    for feature in features:
        if feature["entity"] not in entity_ids:
            errors.append(f"unknown entity for feature {feature['feature_id']}")
        if feature["lifecycle_status"] not in statuses:
            errors.append(f"invalid feature status {feature['feature_id']}")
        for field in ("event_time_column", "availability_time_column", "point_in_time_rule"):
            if not feature.get(field):
                errors.append(f"missing {field} for feature {feature['feature_id']}")
        if feature["feature_name"] in {
            "priority_score",
            "priority_band",
            "material_remediation_required",
        }:
            errors.append(f"leakage feature registered: {feature['feature_id']}")
    feature_id_set = set(feature_ids)
    for view in views:
        if view["entity"] not in entity_ids:
            errors.append(f"unknown entity for view {view['feature_view_id']}")
        for feature_id in view["features"]:
            if feature_id not in feature_id_set:
                errors.append(f"unknown feature {feature_id} in view {view['feature_view_id']}")
    for feature_set in sets:
        for feature_id in feature_set["features"]:
            if feature_id not in feature_id_set:
                errors.append(
                    f"unknown feature {feature_id} in set {feature_set['feature_set_id']}"
                )
    valid_set_versions = {(item["feature_set_id"], item["version"]) for item in sets}
    for consumer in consumers:
        if (consumer["feature_set_id"], consumer["feature_set_version"]) not in valid_set_versions:
            errors.append(
                f"consumer references unknown feature set version: {consumer['consumer_id']}"
            )
    return {
        "valid": not errors,
        "errors": errors,
        "entity_count": len(entities),
        "feature_count": len(features),
        "feature_view_count": len(views),
        "feature_set_count": len(sets),
        "consumer_count": len(consumers),
    }


def _prior_events(
    rows: list[dict[str, str]],
    current: dict[str, str],
    *,
    days: int,
    key: str,
) -> list[dict[str, str]]:
    observation = _parse_timestamp(current["observation_timestamp"])
    start = observation - timedelta(days=days)
    values = []
    for row in rows:
        event_time = _parse_timestamp(row["event_time"])
        availability = _parse_timestamp(row["availability_time"])
        if row[key] != current[key]:
            continue
        if start <= event_time < observation and availability <= observation:
            values.append(row)
    return sorted(values, key=lambda item: (item["event_time"], item["entity_key"]))


def _feature_row(rows: list[dict[str, str]], current: dict[str, str]) -> dict[str, str]:
    exception_history = _prior_events(rows, current, days=90, key="affected_object_type")
    source_history = _prior_events(rows, current, days=30, key="source_system")
    payer_history = _prior_events(rows, current, days=90, key="payer_context")
    high_count = sum(row["severity"] in {"HIGH", "CRITICAL"} for row in exception_history)
    value_at_risk = sum(float(row["financial_value_at_risk"]) for row in exception_history)
    failure_count = sum(row["control_status"] == "FAIL" for row in source_history)
    failure_rate = failure_count / len(source_history) if source_history else 0.0
    latest_source_time = max(
        [_parse_timestamp(row["availability_time"]) for row in exception_history],
        default=None,
    )
    return {
        "entity_key": current["entity_key"],
        "observation_timestamp": current["observation_timestamp"],
        "feature_set_id": FEATURE_SET_ID,
        "feature_set_version": FEATURE_SET_VERSION,
        "prior_exception_count_90d": str(len(exception_history)),
        "prior_high_severity_exception_count_90d": str(high_count),
        "prior_value_at_risk_90d": f"{value_at_risk:.2f}",
        "source_system_failure_rate_30d": f"{failure_rate:.4f}",
        "payer_prior_exception_count_90d": str(len(payer_history)),
        "feature_timestamp": latest_source_time.isoformat() if latest_source_time else "",
        "freshness_status": "FRESH" if exception_history else "NOT_APPLICABLE",
        "missing_feature_status": "AVAILABLE" if exception_history else "NO_PRIOR_HISTORY",
        "source_lineage": "reconciliation_exception,reconciliation_control_result",
        "retrieval_timestamp": "2025-01-01T00:00:00+00:00",
        "synthetic_flag": "true",
    }


def _write_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_checksums(path: Path, files: list[Path], output_dir: Path) -> Path:
    lines = [
        f"{_sha256(file)}  {file.relative_to(output_dir).as_posix()}" for file in sorted(files)
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_reference_outputs(
    output_dir: Path,
    *,
    fixture_path: Path = DEFAULT_FIXTURE,
    overwrite: bool = False,
) -> FeatureStoreReferenceResult:
    """Build deterministic historical and scoring retrieval outputs."""
    if output_dir.exists():
        if not overwrite:
            raise ValueError(f"output directory already exists: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    registry_report = validate_registry()
    if not registry_report["valid"]:
        raise ValueError(f"invalid feature registry: {registry_report['errors']}")
    events = _load_events(fixture_path)
    rows = [_feature_row(events, event) for event in events]
    training_rows = rows[:7]
    scoring_rows = rows[7:]

    entity_registry = _write_json(
        output_dir / "entity_registry.json",
        _read_yaml(REGISTRY_ROOT / "entities.yaml"),
    )
    feature_registry = _write_json(
        output_dir / "feature_registry.json",
        _read_yaml(REGISTRY_ROOT / "features.yaml"),
    )
    feature_view_registry = _write_json(
        output_dir / "feature_view_registry.json",
        _read_yaml(REGISTRY_ROOT / "feature_views.yaml"),
    )
    feature_set_registry = _write_json(
        output_dir / "feature_set_registry.json",
        _read_yaml(REGISTRY_ROOT / "feature_sets.yaml"),
    )
    historical_training_set = _write_csv(output_dir / "historical_training_set.csv", training_rows)
    batch_scoring_set = _write_csv(output_dir / "batch_scoring_set.csv", scoring_rows)
    validation_report = _write_json(
        output_dir / "validation_report.json",
        {
            **registry_report,
            "point_in_time_valid": True,
            "historical_training_rows": len(training_rows),
            "batch_scoring_rows": len(scoring_rows),
            "feature_set_id": FEATURE_SET_ID,
            "feature_set_version": FEATURE_SET_VERSION,
            "snowflake_connected": False,
            "dataiku_connected": False,
            "online_serving": "deferred",
        },
    )
    validation_report_md = output_dir / "validation_report.md"
    validation_report_md.write_text(
        "# Feature store reference validation\n\n"
        "- Registry valid: true\n"
        "- Point-in-time valid: true\n"
        "- Snowflake connected: false\n"
        "- Online serving: deferred\n",
        encoding="utf-8",
    )
    retrieval_manifest = _write_json(
        output_dir / "retrieval_manifest.json",
        {
            "run_id": "m12-feature-store-reference-2025-01-01",
            "generated_at": datetime(2025, 1, 1, tzinfo=UTC).isoformat(),
            "fixture": fixture_path.as_posix(),
            "fixture_sha256": _sha256(fixture_path),
            "feature_set_id": FEATURE_SET_ID,
            "feature_set_version": FEATURE_SET_VERSION,
            "mode": "local_reference",
            "synthetic": True,
            "not_snowflake_materialised": True,
            "not_online_served": True,
        },
    )
    checksums = _write_checksums(
        output_dir / "checksums.sha256",
        [
            entity_registry,
            feature_registry,
            feature_view_registry,
            feature_set_registry,
            historical_training_set,
            batch_scoring_set,
            retrieval_manifest,
            validation_report,
            validation_report_md,
        ],
        output_dir,
    )
    return FeatureStoreReferenceResult(
        output_dir=output_dir,
        retrieval_manifest=retrieval_manifest,
        validation_report=validation_report,
        historical_training_set=historical_training_set,
        batch_scoring_set=batch_scoring_set,
        checksums=checksums,
    )
