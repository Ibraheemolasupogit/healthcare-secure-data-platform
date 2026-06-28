"""Safe Airflow callbacks for local structured failure metadata."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def failure_record(context: dict[str, Any], output_root: Path, execution_mode: str) -> dict[str, Any]:
    task_instance = context.get("task_instance")
    exception = context.get("exception")
    dag = context.get("dag")
    record = {
        "dag_id": getattr(dag, "dag_id", context.get("dag_id", "unknown")),
        "task_id": getattr(task_instance, "task_id", context.get("task_id", "unknown")),
        "run_id": context.get("run_id", "unknown"),
        "logical_date": str(context.get("logical_date", "")),
        "try_number": getattr(task_instance, "try_number", None),
        "exception_class": exception.__class__.__name__ if exception else None,
        "execution_mode": execution_mode,
        "batch_id": context.get("params", {}).get("batch_id", "airflow_context"),
        "timestamp": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "synthetic_flag": True,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    with (output_root / "failure_events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def build_failure_callback(output_root: Path, execution_mode: str):
    """Return an Airflow-compatible callback without external notification side effects."""

    def _callback(context: dict[str, Any]) -> None:
        failure_record(context, output_root, execution_mode)

    return _callback
