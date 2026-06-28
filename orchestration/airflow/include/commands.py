"""Safe command construction for Airflow tasks."""

from __future__ import annotations

import shlex
from pathlib import Path

from configuration import AirflowPlatformConfig, selector_for


def _quote(parts: list[str]) -> str:
    return shlex.join(parts)


def healthcare_platform_command(*parts: str) -> str:
    """Build a shell-safe healthcare-platform CLI command."""
    return _quote(["healthcare-platform", *parts])


def generate_sources_command(config: AirflowPlatformConfig, output_dir: Path) -> str:
    parts = [
        "generate",
        "--profile",
        config.profile,
        "--seed",
        str(config.seed),
        "--reference-date",
        config.reference_date.isoformat(),
        "--output-dir",
        str(output_dir),
    ]
    if config.overwrite_outputs:
        parts.append("--overwrite")
    return healthcare_platform_command(*parts)


def validate_data_command(input_dir: Path) -> str:
    return healthcare_platform_command("validate-data", "--input-dir", str(input_dir))


def validate_billing_command(input_dir: Path) -> str:
    return healthcare_platform_command("validate-billing", "--input-dir", str(input_dir))


def interoperability_command(command: str, *parts: str) -> str:
    return healthcare_platform_command("interoperability", command, *parts)


def process_interoperability_batch_command(
    config: AirflowPlatformConfig, input_dir: Path, output_dir: Path
) -> str:
    parts = [
        "--input-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--seed",
        str(config.seed),
    ]
    if config.overwrite_outputs:
        parts.append("--overwrite")
    return interoperability_command("process-batch", *parts)


def snowflake_render_command(output_dir: Path) -> str:
    return healthcare_platform_command(
        "snowflake-render", "--environment", "DEV", "--output-dir", str(output_dir), "--overwrite"
    )


def snowflake_validate_command() -> str:
    return healthcare_platform_command("snowflake-validate")


def dbt_parse_command(config: AirflowPlatformConfig) -> str:
    return _quote(["dbt", "parse", "--profiles-dir", str(config.dbt_profiles_dir), "--no-partial-parse"])


def dbt_build_command(config: AirflowPlatformConfig, layer: str) -> str:
    return _quote(
        [
            "dbt",
            "build",
            "--select",
            selector_for(layer),
            "--profiles-dir",
            str(config.dbt_profiles_dir),
            "--target",
            config.dbt_target,
        ]
    )


def dbt_source_freshness_command(config: AirflowPlatformConfig) -> str:
    return _quote(
        [
            "dbt",
            "source",
            "freshness",
            "--profiles-dir",
            str(config.dbt_profiles_dir),
            "--target",
            config.dbt_target,
        ]
    )


def dbt_docs_generate_command(config: AirflowPlatformConfig) -> str:
    return _quote(
        [
            "dbt",
            "docs",
            "generate",
            "--profiles-dir",
            str(config.dbt_profiles_dir),
            "--target",
            config.dbt_target,
        ]
    )


def assurance_evidence_command(output_dir: Path, overwrite: bool = True) -> str:
    parts = ["assurance-evidence", "--output-dir", str(output_dir)]
    if overwrite:
        parts.append("--overwrite")
    return healthcare_platform_command(*parts)


def command_environment(config: AirflowPlatformConfig) -> dict[str, str]:
    return {
        "HEALTHCARE_PLATFORM_ENV": config.environment,
        "HEALTHCARE_AIRFLOW_EXECUTION_MODE": config.execution_mode,
        "PYTHONPATH": str(config.repository_root / "src"),
    }
