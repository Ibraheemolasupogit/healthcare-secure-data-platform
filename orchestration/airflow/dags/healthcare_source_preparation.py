"""Prepare deterministic synthetic healthcare source data."""

from __future__ import annotations

from _common import CONFIG, bash_task, create_dag, file_sensor, marker, python_task
from commands import generate_sources_command, validate_data_command
from validation import require_fixture_dataset, verify_checksum_manifest

dag = create_dag(
    "healthcare_source_preparation",
    schedule="@daily",
    description="Validate or generate deterministic synthetic healthcare source data.",
)

with dag:
    validate_runtime_configuration = python_task(
        "validate_runtime_configuration", lambda: (_ for _ in ()).throw(ValueError(CONFIG.validate()))
        if CONFIG.validate()
        else "configuration valid"
    )
    check_output_target = marker("check_output_target")
    check_fixture_manifest = file_sensor("check_fixture_manifest", CONFIG.source_data_path / "manifest.json")
    verify_fixture_dataset = python_task(
        "verify_manifest", require_fixture_dataset, path=CONFIG.source_data_path
    )
    generate_small_or_configured_profile = bash_task(
        "generate_small_or_configured_profile",
        generate_sources_command(
            CONFIG,
            CONFIG.output_path("source_preparation", "{{ ds }}") / "synthetic_sources",
        ),
    )
    validate_generated_data = bash_task(
        "validate_generated_data",
        validate_data_command(CONFIG.source_data_path),
    )
    verify_checksums = python_task(
        "verify_checksums", verify_checksum_manifest, directory=CONFIG.source_data_path
    )
    publish_source_preparation_evidence = marker("publish_source_preparation_evidence")

    (
        validate_runtime_configuration
        >> check_output_target
        >> check_fixture_manifest
        >> verify_fixture_dataset
        >> generate_small_or_configured_profile
        >> validate_generated_data
        >> verify_checksums
        >> publish_source_preparation_evidence
    )
