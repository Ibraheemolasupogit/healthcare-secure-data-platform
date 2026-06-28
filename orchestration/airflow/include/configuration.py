"""Typed configuration for local-first Airflow orchestration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from constants import DBT_SELECTORS, SUPPORTED_EXECUTION_MODES


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AirflowPlatformConfig:
    """Single authoritative Milestone 10 orchestration configuration."""

    environment: str
    execution_mode: str
    repository_root: Path
    output_root: Path
    profile: str
    seed: int
    reference_date: date
    source_data_path: Path
    interoperability_path: Path
    assurance_evidence_output: Path
    dbt_project_dir: Path
    dbt_profiles_dir: Path
    dbt_target: str
    connected_snowflake_enabled: bool
    allow_large_generation: bool
    overwrite_outputs: bool
    retry_count: int
    retry_delay_seconds: int
    execution_timeout_minutes: int
    sensor_timeout_seconds: int
    sensor_poke_interval_seconds: int
    catchup: bool
    max_active_runs: int
    notification_integrations_enabled: bool

    @property
    def retry_delay(self) -> timedelta:
        return timedelta(seconds=self.retry_delay_seconds)

    @property
    def execution_timeout(self) -> timedelta:
        return timedelta(minutes=self.execution_timeout_minutes)

    def output_path(self, workflow: str, logical_date: str) -> Path:
        safe_logical_date = logical_date.replace(":", "").replace("+", "_")
        return self.output_root / workflow / safe_logical_date

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.execution_mode not in SUPPORTED_EXECUTION_MODES:
            errors.append(f"unsupported execution mode: {self.execution_mode}")
        if self.execution_mode == "connected_snowflake" and not self.connected_snowflake_enabled:
            errors.append("connected Snowflake mode requires explicit enablement")
        if self.profile == "large" and not self.allow_large_generation:
            errors.append("large generation is disabled by default")
        if self.overwrite_outputs and self.execution_mode == "fixture":
            errors.append("fixture mode cannot overwrite committed inputs")
        if self.retry_count < 0 or self.retry_count > 5:
            errors.append("retry count must be between 0 and 5")
        if self.execution_timeout_minutes <= 0:
            errors.append("execution timeout must be positive")
        if self.sensor_timeout_seconds <= 0:
            errors.append("sensor timeout must be positive")
        if self.max_active_runs <= 0:
            errors.append("max active runs must be positive")
        if self.notification_integrations_enabled:
            errors.append("external notifications are disabled for Milestone 10")
        if not self.repository_root.exists():
            errors.append(f"repository root does not exist: {self.repository_root}")
        if not self.dbt_project_dir.exists():
            errors.append(f"dbt project directory does not exist: {self.dbt_project_dir}")
        if not self.dbt_profiles_dir.exists():
            errors.append(f"dbt profiles directory does not exist: {self.dbt_profiles_dir}")
        return errors


def load_config() -> AirflowPlatformConfig:
    """Load orchestration configuration from environment variables."""
    repo = Path(os.getenv("HEALTHCARE_AIRFLOW_REPOSITORY_ROOT", ".")).resolve()
    output_root = Path(os.getenv("HEALTHCARE_AIRFLOW_OUTPUT_ROOT", "outputs/orchestration"))
    output_root = output_root if output_root.is_absolute() else repo / output_root
    source_path = Path(os.getenv("HEALTHCARE_AIRFLOW_SOURCE_DATA_PATH", "data/samples/small"))
    interop_path = Path(
        os.getenv("HEALTHCARE_AIRFLOW_INTEROPERABILITY_PATH", "data/samples/interoperability")
    )
    evidence_output = Path(
        os.getenv("HEALTHCARE_AIRFLOW_ASSURANCE_EVIDENCE_OUTPUT", "outputs/orchestration/assurance")
    )
    return AirflowPlatformConfig(
        environment=os.getenv("HEALTHCARE_PLATFORM_ENV", "local"),
        execution_mode=os.getenv("HEALTHCARE_AIRFLOW_EXECUTION_MODE", "fixture"),
        repository_root=repo,
        output_root=output_root,
        profile=os.getenv("HEALTHCARE_AIRFLOW_PROFILE", "small"),
        seed=int(os.getenv("HEALTHCARE_AIRFLOW_SEED", "42")),
        reference_date=date.fromisoformat(os.getenv("HEALTHCARE_AIRFLOW_REFERENCE_DATE", "2025-01-01")),
        source_data_path=source_path if source_path.is_absolute() else repo / source_path,
        interoperability_path=interop_path if interop_path.is_absolute() else repo / interop_path,
        assurance_evidence_output=(
            evidence_output if evidence_output.is_absolute() else repo / evidence_output
        ),
        dbt_project_dir=repo / os.getenv("HEALTHCARE_AIRFLOW_DBT_PROJECT_DIR", "dbt"),
        dbt_profiles_dir=repo / os.getenv("HEALTHCARE_AIRFLOW_DBT_PROFILES_DIR", "dbt"),
        dbt_target=os.getenv("HEALTHCARE_AIRFLOW_DBT_TARGET", "dev"),
        connected_snowflake_enabled=_bool_env("HEALTHCARE_AIRFLOW_CONNECTED_SNOWFLAKE", False),
        allow_large_generation=_bool_env("HEALTHCARE_AIRFLOW_ALLOW_LARGE_GENERATION", False),
        overwrite_outputs=_bool_env("HEALTHCARE_AIRFLOW_OVERWRITE", False),
        retry_count=int(os.getenv("HEALTHCARE_AIRFLOW_RETRY_COUNT", "1")),
        retry_delay_seconds=int(os.getenv("HEALTHCARE_AIRFLOW_RETRY_DELAY_SECONDS", "60")),
        execution_timeout_minutes=int(os.getenv("HEALTHCARE_AIRFLOW_EXECUTION_TIMEOUT_MINUTES", "30")),
        sensor_timeout_seconds=int(os.getenv("HEALTHCARE_AIRFLOW_SENSOR_TIMEOUT_SECONDS", "30")),
        sensor_poke_interval_seconds=int(
            os.getenv("HEALTHCARE_AIRFLOW_SENSOR_POKE_INTERVAL_SECONDS", "5")
        ),
        catchup=_bool_env("HEALTHCARE_AIRFLOW_CATCHUP", False),
        max_active_runs=int(os.getenv("HEALTHCARE_AIRFLOW_MAX_ACTIVE_RUNS", "1")),
        notification_integrations_enabled=_bool_env(
            "HEALTHCARE_AIRFLOW_ENABLE_NOTIFICATIONS", False
        ),
    )


def selector_for(layer: str) -> str:
    """Return the authoritative dbt selector for an orchestration layer."""
    return DBT_SELECTORS[layer]
