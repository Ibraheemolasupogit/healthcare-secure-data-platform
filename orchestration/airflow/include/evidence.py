"""Deterministic orchestration evidence helpers."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkflowRunManifest:
    workflow_run_id: str
    dag_id: str
    logical_date: str
    data_interval_start: str
    data_interval_end: str
    execution_mode: str
    environment: str
    source_profile: str
    seed: int
    reference_date: str
    task_count: int
    successful_task_count: int
    skipped_task_count: int
    failed_task_count: int
    connected_execution_status: str
    synthetic_flag: bool
    limitations: list[str]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_workflow_manifest(output_dir: Path, manifest: WorkflowRunManifest) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "workflow_run_manifest.json"
    path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_task_summary(output_dir: Path, rows: list[dict[str, str]]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "task_execution_summary.csv"
    fieldnames = ["dag_id", "task_id", "status", "contract", "execution_mode"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_checksums(output_dir: Path, files: list[Path]) -> Path:
    path = output_dir / "checksums.sha256"
    lines = [f"{sha256_file(file)}  {file.relative_to(output_dir).as_posix()}" for file in files]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
