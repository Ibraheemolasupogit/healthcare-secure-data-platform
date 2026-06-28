"""Deterministic Milestone 9 assurance evidence-pack generation."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DBT_ROOT = Path("dbt")
ASSURANCE_MODEL_ROOT = DBT_ROOT / "models"
ASSURANCE_SEED_ROOT = DBT_ROOT / "seeds" / "assurance"


@dataclass(frozen=True)
class EvidencePack:
    """Generated assurance evidence-pack file paths."""

    output_dir: Path
    manifest_path: Path
    inventory_path: Path
    summary_path: Path
    checksum_path: Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalise_path(path: Path) -> str:
    return path.as_posix()


def _assurance_files(root: Path) -> list[Path]:
    candidates = [
        *root.glob("dbt/models/intermediate/assurance/**/*.sql"),
        *root.glob("dbt/models/curated/assurance/**/*.sql"),
        *root.glob("dbt/models/**/assurance/_schema.yml"),
        *root.glob("dbt/macros/assurance/*.sql"),
        *root.glob("dbt/seeds/assurance/*.csv"),
        *root.glob("dbt/seeds/assurance/_schema.yml"),
    ]
    return sorted(path for path in candidates if path.is_file())


def _read_manifest_counts(root: Path) -> dict[str, int] | None:
    manifest_path = root / "dbt" / "target" / "manifest.json"
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    nodes = manifest.get("nodes", {})
    macros = manifest.get("macros", {})
    assurance_nodes = []
    for node in nodes.values():
        original_file_path = node.get("original_file_path", "")
        if "assurance" in node.get("tags", []) or "/assurance/" in original_file_path:
            assurance_nodes.append(node)
    return {
        "assurance_nodes": len(assurance_nodes),
        "models": sum(node.get("resource_type") == "model" for node in assurance_nodes),
        "seeds": sum(node.get("resource_type") == "seed" for node in assurance_nodes),
        "tests": sum(node.get("resource_type") == "test" for node in assurance_nodes),
        "assurance_macros": sum(
            "/macros/assurance/" in macro.get("original_file_path", "") for macro in macros.values()
        ),
    }


def _seed_row_counts(root: Path) -> dict[str, int]:
    row_counts: dict[str, int] = {}
    for path in sorted((root / ASSURANCE_SEED_ROOT).glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            row_counts[path.stem] = sum(1 for _ in csv.DictReader(handle))
    return row_counts


def _inventory(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in _assurance_files(root):
        relative_path = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        records.append(
            {
                "path": _normalise_path(relative_path),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "line_count": text.count("\n") + (0 if text.endswith("\n") else 1),
            }
        )
    return records


def _write_inventory_csv(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256", "line_count"])
        writer.writeheader()
        writer.writerows(records)


def _write_summary(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Milestone 9 assurance evidence pack",
        "",
        f"Generated at: `{manifest['generated_at']}`",
        "",
        "## Scope",
        "",
        "- Reconciliation control results.",
        "- Exception ownership, lifecycle, prioritisation and remediation status.",
        "- Revenue-at-risk summaries and assurance evidence views.",
        "- Deterministic seed-driven tolerance, ownership, severity, lifecycle and priority rules.",
        "",
        "## Source boundary",
        "",
        "The pack records assurance artefacts only. Runtime assurance models reference "
        "Milestone 8 curated billing and finance controls through `ref()` and do not query "
        "raw sources directly.",
        "",
        "## Inventory",
        "",
        f"- Files inventoried: {manifest['file_count']}",
        f"- Seed row counts: `{json.dumps(manifest['seed_row_counts'], sort_keys=True)}`",
        f"- dbt manifest counts: `{json.dumps(manifest['dbt_manifest_counts'], sort_keys=True)}`",
        "",
        "## Checksum",
        "",
        f"- Manifest SHA-256: `{manifest['manifest_sha256']}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_checksums(path: Path, files: list[Path], output_dir: Path) -> None:
    rows = []
    for file_path in sorted(files):
        rows.append(f"{_sha256(file_path)}  {file_path.relative_to(output_dir).as_posix()}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_evidence_pack(
    output_dir: Path,
    *,
    project_root: Path = Path("."),
    overwrite: bool = False,
) -> EvidencePack:
    """Write a deterministic local assurance evidence pack."""
    root = project_root.resolve()
    destination = output_dir.resolve()
    if destination.exists():
        if not overwrite:
            raise ValueError(f"output directory already exists: {destination}")
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    records = _inventory(root)
    if not records:
        raise ValueError("no Milestone 9 assurance files were found")

    inventory_path = destination / "assurance_inventory.csv"
    manifest_path = destination / "assurance_evidence_manifest.json"
    summary_path = destination / "assurance_evidence_summary.md"
    checksum_path = destination / "checksums.sha256"

    _write_inventory_csv(inventory_path, records)
    manifest: dict[str, Any] = {
        "generated_at": "2025-01-01T00:00:00+00:00",
        "milestone": "9",
        "scope": "healthcare billing reconciliation, exception management and revenue assurance",
        "source_boundary": "curated_assurance_models_reference_milestone_8_outputs",
        "file_count": len(records),
        "seed_row_counts": _seed_row_counts(root),
        "dbt_manifest_counts": _read_manifest_counts(root),
        "files": records,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest["manifest_sha256"] = _sha256(manifest_path)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_summary(summary_path, manifest)
    _write_checksums(checksum_path, [manifest_path, inventory_path, summary_path], destination)
    return EvidencePack(
        output_dir=destination,
        manifest_path=manifest_path,
        inventory_path=inventory_path,
        summary_path=summary_path,
        checksum_path=checksum_path,
    )
