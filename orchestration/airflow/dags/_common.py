"""Shared Airflow DAG construction helpers."""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.task_group import TaskGroup
from airflow.utils.timezone import datetime

AIRFLOW_ROOT = Path(__file__).resolve().parents[1]
INCLUDE_ROOT = AIRFLOW_ROOT / "include"
if str(INCLUDE_ROOT) not in sys.path:
    sys.path.insert(0, str(INCLUDE_ROOT))

from callbacks import build_failure_callback  # noqa: E402
from commands import command_environment  # noqa: E402
from configuration import AirflowPlatformConfig, load_config  # noqa: E402
from constants import DEFAULT_START_DATE, MILESTONE_10_TAGS  # noqa: E402
from validation import require_path  # noqa: E402


CONFIG = load_config()


def default_args(config: AirflowPlatformConfig = CONFIG) -> dict[str, object]:
    return {
        "owner": "analytics-engineering",
        "retries": config.retry_count,
        "retry_delay": config.retry_delay,
        "execution_timeout": config.execution_timeout,
        "on_failure_callback": build_failure_callback(
            config.output_root / "failures", config.execution_mode
        ),
    }


def create_dag(dag_id: str, schedule: str | None, description: str) -> DAG:
    return DAG(
        dag_id=dag_id,
        description=description,
        start_date=datetime.fromisoformat(DEFAULT_START_DATE),
        schedule=schedule,
        catchup=CONFIG.catchup,
        max_active_runs=CONFIG.max_active_runs,
        default_args=default_args(),
        tags=list(MILESTONE_10_TAGS),
        doc_md=(
            "Milestone 10 local-first orchestration. Airflow coordinates existing "
            "CLI/dbt contracts and does not own healthcare business logic."
        ),
    )


def bash_task(task_id: str, command: str, cwd: Path | None = None) -> BashOperator:
    return BashOperator(
        task_id=task_id,
        bash_command=command,
        cwd=str(cwd or CONFIG.repository_root),
        env=command_environment(CONFIG),
        append_env=True,
    )


def python_task(task_id: str, callable_object, **op_kwargs: object) -> PythonOperator:
    return PythonOperator(task_id=task_id, python_callable=callable_object, op_kwargs=op_kwargs)


def file_sensor(task_id: str, path: Path) -> FileSensor:
    return FileSensor(
        task_id=task_id,
        filepath=str(path),
        poke_interval=CONFIG.sensor_poke_interval_seconds,
        timeout=CONFIG.sensor_timeout_seconds,
        mode="poke",
    )


def connected_mode_gate(task_id: str) -> ShortCircuitOperator:
    return ShortCircuitOperator(
        task_id=task_id,
        python_callable=lambda: CONFIG.connected_snowflake_enabled,
        ignore_downstream_trigger_rules=False,
    )


def check_path_task(task_id: str, path: Path) -> PythonOperator:
    return python_task(task_id, require_path, path=path)


def marker(task_id: str) -> EmptyOperator:
    return EmptyOperator(task_id=task_id, execution_timeout=timedelta(minutes=5))


__all__ = [
    "CONFIG",
    "TaskGroup",
    "bash_task",
    "check_path_task",
    "connected_mode_gate",
    "create_dag",
    "file_sensor",
    "marker",
    "python_task",
]
