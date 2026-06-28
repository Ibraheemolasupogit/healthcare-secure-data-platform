"""Coordinate bounded synthetic FHIR and HL7 interoperability processing."""

from __future__ import annotations

from _common import CONFIG, bash_task, create_dag, file_sensor, marker, python_task
from commands import interoperability_command, process_interoperability_batch_command
from validation import require_interoperability_fixture, require_path

dag = create_dag(
    "interoperability_ingestion",
    schedule=None,
    description="Validate committed interoperability fixtures and process deterministic batches.",
)

with dag:
    check_interoperability_inputs = python_task(
        "check_interoperability_inputs",
        require_interoperability_fixture,
        path=CONFIG.interoperability_path,
    )
    check_ingestion_manifest = file_sensor(
        "check_ingestion_manifest", CONFIG.interoperability_path / "manifests/ingestion_manifest.json"
    )
    validate_fhir = bash_task(
        "validate_fhir",
        interoperability_command("validate-fhir", "--input-dir", str(CONFIG.interoperability_path / "fhir")),
    )
    validate_hl7 = bash_task(
        "validate_hl7",
        interoperability_command("validate-hl7", "--input-dir", str(CONFIG.interoperability_path / "hl7")),
    )
    process_interoperability_batch = bash_task(
        "process_interoperability_batch",
        process_interoperability_batch_command(
            CONFIG,
            CONFIG.source_data_path / "relational",
            CONFIG.output_path("interoperability", "{{ ds }}"),
        ),
    )
    validate_crosswalk = python_task(
        "validate_crosswalk",
        require_path,
        path=CONFIG.interoperability_path / "crosswalks/identifier_crosswalk.json",
    )
    validate_quarantine = python_task(
        "validate_quarantine",
        require_path,
        path=CONFIG.interoperability_path / "quarantine/quarantine_records.json",
    )
    publish_interoperability_evidence = marker("publish_interoperability_evidence")

    check_interoperability_inputs >> check_ingestion_manifest >> [validate_fhir, validate_hl7]
    [validate_fhir, validate_hl7] >> process_interoperability_batch
    process_interoperability_batch >> [validate_crosswalk, validate_quarantine]
    [validate_crosswalk, validate_quarantine] >> publish_interoperability_evidence
