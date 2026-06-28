"""Demonstrate the complete local-first platform dependency chain."""

from __future__ import annotations

from _common import CONFIG, TaskGroup, bash_task, create_dag, marker
from commands import (
    assurance_evidence_command,
    dbt_build_command,
    dbt_parse_command,
    interoperability_command,
    validate_data_command,
)

dag = create_dag(
    "healthcare_platform_end_to_end",
    schedule=None,
    description="Manual end-to-end dependency demonstration without duplicating domain logic.",
)

with dag:
    with TaskGroup("source_preparation") as source_preparation:
        validate_sources = bash_task("validate_sources", validate_data_command(CONFIG.source_data_path))

    with TaskGroup("interoperability_ingestion") as interoperability_ingestion:
        validate_fhir = bash_task(
            "validate_fhir",
            interoperability_command("validate-fhir", "--input-dir", str(CONFIG.interoperability_path / "fhir")),
        )
        validate_hl7 = bash_task(
            "validate_hl7",
            interoperability_command("validate-hl7", "--input-dir", str(CONFIG.interoperability_path / "hl7")),
        )

    with TaskGroup("platform_preflight") as platform_preflight:
        parse_dbt_project = bash_task(
            "parse_dbt_project", dbt_parse_command(CONFIG), cwd=CONFIG.dbt_project_dir
        )

    with TaskGroup("dbt_staging") as dbt_staging:
        run_staging = bash_task(
            "run_staging", dbt_build_command(CONFIG, "staging"), cwd=CONFIG.dbt_project_dir
        )

    with TaskGroup("dbt_core") as dbt_core:
        run_core = bash_task("run_core", dbt_build_command(CONFIG, "core"), cwd=CONFIG.dbt_project_dir)

    with TaskGroup("dbt_billing_finance") as dbt_billing_finance:
        run_billing = bash_task(
            "run_billing", dbt_build_command(CONFIG, "billing"), cwd=CONFIG.dbt_project_dir
        )
        run_finance = bash_task(
            "run_finance", dbt_build_command(CONFIG, "finance"), cwd=CONFIG.dbt_project_dir
        )

    with TaskGroup("dbt_assurance") as dbt_assurance:
        run_assurance = bash_task(
            "run_assurance", dbt_build_command(CONFIG, "assurance"), cwd=CONFIG.dbt_project_dir
        )

    with TaskGroup("assurance_evidence") as assurance_evidence:
        generate_evidence = bash_task(
            "generate_evidence", assurance_evidence_command(CONFIG.assurance_evidence_output, overwrite=True)
        )

    platform_run_summary = marker("platform_run_summary")

    (
        source_preparation
        >> interoperability_ingestion
        >> platform_preflight
        >> dbt_staging
        >> dbt_core
        >> dbt_billing_finance
        >> dbt_assurance
        >> assurance_evidence
        >> platform_run_summary
    )
