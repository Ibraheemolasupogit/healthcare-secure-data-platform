"""Coordinate dbt platform layers in dependency order."""

from __future__ import annotations

from _common import CONFIG, TaskGroup, bash_task, connected_mode_gate, create_dag, marker
from commands import (
    dbt_build_command,
    dbt_docs_generate_command,
    dbt_parse_command,
    dbt_source_freshness_command,
)

dag = create_dag(
    "healthcare_dbt_pipeline",
    schedule="@daily",
    description="Orchestrate dbt parse/local checks and optional connected layer builds.",
)

with dag:
    with TaskGroup("dbt_preflight") as dbt_preflight:
        parse_project = bash_task("parse_project", dbt_parse_command(CONFIG), cwd=CONFIG.dbt_project_dir)
        connected_mode_enabled = connected_mode_gate("connected_mode_enabled")
        parse_project >> connected_mode_enabled

    with TaskGroup("source_freshness") as source_freshness:
        run_source_freshness = bash_task(
            "run_source_freshness",
            dbt_source_freshness_command(CONFIG),
            cwd=CONFIG.dbt_project_dir,
        )

    with TaskGroup("staging") as staging:
        run_staging_models = bash_task(
            "run_staging_models", dbt_build_command(CONFIG, "staging"), cwd=CONFIG.dbt_project_dir
        )

    with TaskGroup("healthcare_core") as healthcare_core:
        run_core_models = bash_task(
            "run_core_models", dbt_build_command(CONFIG, "core"), cwd=CONFIG.dbt_project_dir
        )

    with TaskGroup("billing_finance") as billing_finance:
        run_billing_models = bash_task(
            "run_billing_models", dbt_build_command(CONFIG, "billing"), cwd=CONFIG.dbt_project_dir
        )
        run_finance_models = bash_task(
            "run_finance_models", dbt_build_command(CONFIG, "finance"), cwd=CONFIG.dbt_project_dir
        )

    with TaskGroup("assurance") as assurance:
        run_assurance_models = bash_task(
            "run_assurance_models",
            dbt_build_command(CONFIG, "assurance"),
            cwd=CONFIG.dbt_project_dir,
        )

    with TaskGroup("dbt_tests") as dbt_tests:
        dbt_layer_tests_complete = marker("dbt_layer_tests_complete")

    with TaskGroup("docs_metadata") as docs_metadata:
        generate_docs_metadata = bash_task(
            "generate_docs_metadata", dbt_docs_generate_command(CONFIG), cwd=CONFIG.dbt_project_dir
        )

    dbt_preflight >> source_freshness >> staging >> healthcare_core >> billing_finance >> assurance
    assurance >> dbt_tests >> docs_metadata
