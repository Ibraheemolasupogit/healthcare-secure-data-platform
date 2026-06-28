"""Coordinate governed billing/finance and assurance evidence workflows."""

from __future__ import annotations

from _common import CONFIG, TaskGroup, bash_task, connected_mode_gate, create_dag, marker
from commands import assurance_evidence_command, dbt_build_command, validate_billing_command

dag = create_dag(
    "billing_assurance_pipeline",
    schedule="@daily",
    description="Coordinate M8 billing/finance outputs and M9 assurance evidence.",
)

with dag:
    validate_billing_inputs = bash_task(
        "validate_billing_inputs", validate_billing_command(CONFIG.source_data_path)
    )
    connected_mode_enabled = connected_mode_gate("connected_mode_enabled")

    with TaskGroup("governed_billing_finance") as governed_billing_finance:
        run_billing_finance_models = [
            bash_task("run_billing_models", dbt_build_command(CONFIG, "billing"), cwd=CONFIG.dbt_project_dir),
            bash_task("run_finance_models", dbt_build_command(CONFIG, "finance"), cwd=CONFIG.dbt_project_dir),
        ]

    with TaskGroup("assurance_controls") as assurance_controls:
        run_assurance_models = bash_task(
            "run_assurance_models",
            dbt_build_command(CONFIG, "assurance"),
            cwd=CONFIG.dbt_project_dir,
        )
        validate_control_results = marker("validate_control_results")
        validate_exception_outputs = marker("validate_exception_outputs")
        run_assurance_models >> [validate_control_results, validate_exception_outputs]

    generate_assurance_evidence = bash_task(
        "generate_assurance_evidence",
        assurance_evidence_command(CONFIG.assurance_evidence_output, overwrite=True),
    )
    verify_evidence_checksums = bash_task(
        "verify_evidence_checksums",
        f"cd {CONFIG.assurance_evidence_output} && shasum -a 256 -c checksums.sha256",
    )
    publish_assurance_run_metadata = marker("publish_assurance_run_metadata")

    validate_billing_inputs >> connected_mode_enabled >> governed_billing_finance
    governed_billing_finance >> assurance_controls >> generate_assurance_evidence
    generate_assurance_evidence >> verify_evidence_checksums >> publish_assurance_run_metadata
