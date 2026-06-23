import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from healthcare_platform import cli
from healthcare_platform.interoperability.config import load_config
from healthcare_platform.interoperability.fhir import (
    generate_resources,
    parse_resource,
    validate_bundle,
)
from healthcare_platform.interoperability.hl7 import (
    component,
    generate_messages,
    parse_message,
    validate_message,
)
from healthcare_platform.interoperability.identifiers import CrosswalkEntry, build_crosswalk
from healthcare_platform.interoperability.service import (
    DEFAULT_CANONICAL_INPUT,
    checksum_bytes,
    generate_fhir,
    generate_hl7,
    generate_negative_corpus,
    load_canonical,
    process_batch,
    validate_corpus,
)
from healthcare_platform.interoperability.terminology import map_code


@pytest.fixture
def canonical() -> dict[str, list[dict[str, Any]]]:
    return load_canonical()


def test_fhir_generation_is_deterministic_and_reuses_canonical_ids(
    tmp_path: Path, canonical: dict[str, list[dict[str, Any]]]
) -> None:
    first = generate_fhir(DEFAULT_CANONICAL_INPUT, tmp_path / "first")
    second = generate_fhir(DEFAULT_CANONICAL_INPUT, tmp_path / "second")
    assert {path.relative_to(tmp_path / "first"): path.read_bytes() for path in first} == {
        path.relative_to(tmp_path / "second"): path.read_bytes() for path in second
    }
    resources = generate_resources(canonical, load_config())
    patient = next(item for item in resources if item["resourceType"] == "Patient")
    assert patient["id"] == canonical["patients"][0]["patient_id"]
    assert patient["meta"]["tag"][0]["code"] == "SYNTHETIC-FHIR-INSPIRED"


def test_fhir_bundle_references_resolve(canonical: dict[str, list[dict[str, Any]]]) -> None:
    resources = generate_resources(canonical, load_config())
    bundle = {"entry": [{"resource": item} for item in resources]}
    parsed = validate_bundle(bundle, load_config())
    assert parsed
    assert all(item.status == "ACCEPTED" for item in parsed)
    assert {item.message_type for item in parsed} == set(load_config()["supported_fhir_resources"])


def test_fhir_parser_preserves_unmapped_and_extension_fields(
    canonical: dict[str, list[dict[str, Any]]],
) -> None:
    resource = next(
        item
        for item in generate_resources(canonical, load_config())
        if item["resourceType"] == "Practitioner"
    )
    resource["customField"] = {"safe": "preserved"}
    parsed = parse_resource(resource, load_config())
    assert parsed.status == "ACCEPTED"
    assert parsed.preserved_fields["extension"]
    assert parsed.unmapped_fields["customField"] == {"safe": "preserved"}


@pytest.mark.parametrize(
    ("resource", "code"),
    [
        ({"id": "PAT-000000001", "meta": {}}, "MISSING_RESOURCE_TYPE"),
        (
            {"resourceType": "ImagingStudy", "id": "IMG-000000001", "meta": {}},
            "UNSUPPORTED_RESOURCE",
        ),
        (
            {
                "resourceType": "Patient",
                "id": "PAT-000000001",
                "meta": {"tag": [{"code": "SYNTHETIC-FHIR-INSPIRED"}]},
                "birthDate": "bad-date",
            },
            "MALFORMED_DATE",
        ),
    ],
)
def test_fhir_negative_validation(resource: dict[str, Any], code: str) -> None:
    parsed = parse_resource(resource, load_config())
    assert code in {issue.code for issue in parsed.issues}
    assert parsed.status in {"REJECTED", "UNSUPPORTED"}


def test_hl7_generation_parsing_and_dispatch(
    tmp_path: Path, canonical: dict[str, list[dict[str, Any]]]
) -> None:
    first = generate_hl7(DEFAULT_CANONICAL_INPUT, tmp_path / "first")
    second = generate_hl7(DEFAULT_CANONICAL_INPUT, tmp_path / "second")
    assert [path.read_bytes() for path in first] == [path.read_bytes() for path in second]
    messages = generate_messages(canonical, load_config())
    assert {validate_message(text, load_config()).message_type for _, text in messages} == set(
        load_config()["supported_hl7_messages"]
    )
    parsed = parse_message(messages[0][1])
    assert parsed.first("MSH") is not None
    assert component("PAT-000000001^^^HEDP^PI", 0) == "PAT-000000001"


def test_hl7_extracts_patient_encounter_order_result_and_appointment(
    canonical: dict[str, list[dict[str, Any]]],
) -> None:
    parsed = [
        validate_message(text, load_config())
        for _, text in generate_messages(canonical, load_config())
    ]
    assert all(item.patient_id == "PAT-000000001" for item in parsed)
    assert all(item.encounter_id for item in parsed if item.message_type != "SIU^S12")
    result = next(item for item in parsed if item.message_type == "ORU^R01")
    assert result.mapped_fields["result_value"]
    assert result.mapped_fields["result_unit"]
    appointment = next(item for item in parsed if item.message_type == "SIU^S12")
    assert (
        appointment.mapped_fields["appointment_id"]
        == canonical["appointments"][0]["appointment_id"]
    )


@pytest.mark.parametrize(
    ("message", "code"),
    [
        ("PID|1||PAT-000000001\r", "MISSING_MSH"),
        (
            "MSH|^~\\&|SYN-EPR|SYN-FACILITY|HEDP|HEDP|BAD||ADT^A01|X|T|2.5\r",
            "MALFORMED_TIMESTAMP",
        ),
        (
            "MSH|^~\\&|SYN-EPR|SYN-FACILITY|HEDP|HEDP|20250101120000||ADT^A01|X|T|2.5\r",
            "MISSING_REQUIRED_SEGMENT",
        ),
    ],
)
def test_hl7_negative_validation(message: str, code: str) -> None:
    parsed = validate_message(message, load_config())
    assert code in {issue.code for issue in parsed.issues}
    assert parsed.status == "REJECTED"


def test_crosswalk_is_stable_deduplicated_and_conflict_safe() -> None:
    entry = CrosswalkEntry("FHIR", "SYN-EPR", "PATIENT", "PAT-000000001", "PAT-000000001")
    assert build_crosswalk([entry, entry]) == [entry.as_dict()]
    conflict = CrosswalkEntry("FHIR", "SYN-EPR", "PATIENT", "PAT-000000001", "PAT-000000002")
    with pytest.raises(ValueError, match="conflicting"):
        build_crosswalk([entry, conflict])


def test_terminology_mapping_is_versioned_and_unknown_safe() -> None:
    assert map_code("sex", "FEMALE")["target_code"] == "female"
    assert map_code("sex", "NOT-A-CODE")["mapping_status"] == "UNKNOWN_CODE"
    assert map_code("not-a-set", "X")["mapping_status"] == "UNKNOWN_CODE_SET"


def test_batch_manifest_envelopes_crosswalk_and_checksums_are_deterministic(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    manifest = process_batch(output_dir=first)
    process_batch(output_dir=second)
    assert manifest["accepted_count"] > 0
    assert manifest["rejected_count"] == 0
    assert manifest["quarantine_count"] == 0
    assert manifest["crosswalk_count"] > 0
    first_files = {
        path.relative_to(first): path.read_bytes() for path in first.rglob("*") if path.is_file()
    }
    second_files = {
        path.relative_to(second): path.read_bytes() for path in second.rglob("*") if path.is_file()
    }
    assert first_files == second_files
    for relative_path, digest in manifest["output_checksums"].items():
        assert checksum_bytes((first / relative_path).read_bytes()) == digest
    envelopes = json.loads((first / "canonical/ingestion_envelopes.json").read_text())
    assert all(item["synthetic_flag"] is True for item in envelopes)
    assert all(item["canonical_patient_id"] == item["source_patient_id"] for item in envelopes)


def test_overwrite_protection_and_negative_corpora(tmp_path: Path) -> None:
    output = tmp_path / "positive"
    process_batch(output_dir=output)
    with pytest.raises(ValueError, match="--overwrite"):
        process_batch(output_dir=output)
    negative = tmp_path / "negative"
    generate_negative_corpus(negative)
    assert validate_corpus(negative / "fhir", "FHIR")["valid"] is False
    assert validate_corpus(negative / "hl7", "HL7V2")["valid"] is False
    quarantine = json.loads((negative / "quarantine/quarantine_records.json").read_text())
    assert len(quarantine) == 8
    assert {record["disposition"] for record in quarantine} == {"REJECTED", "UNSUPPORTED"}
    expected = json.loads((negative / "expected_errors.json").read_text())
    for source_format, directory in (("fhir", negative / "fhir"), ("hl7", negative / "hl7")):
        records = {
            Path(record["raw_payload_path"]).name: set(record["validation_errors"])
            for record in quarantine
            if record["raw_payload_path"].startswith(source_format)
        }
        assert directory.exists()
        for filename, codes in expected[source_format].items():
            assert set(codes) <= records[filename]


def test_duplicate_hl7_control_id_is_rejected(
    tmp_path: Path, canonical: dict[str, list[dict[str, Any]]]
) -> None:
    message = generate_messages(canonical, load_config())[0][1]
    directory = tmp_path / "messages"
    directory.mkdir()
    (directory / "one.hl7").write_text(message)
    (directory / "two.hl7").write_text(message)
    report = validate_corpus(tmp_path, "HL7V2")
    assert report["valid"] is False
    assert any(
        issue["code"] == "DUPLICATE_CONTROL_ID"
        for result in report["results"]
        for issue in result["issues"]
    )


def test_cli_batch_validation_negative_exit_and_backward_compatibility(
    tmp_path: Path, capsys: Any
) -> None:
    output = tmp_path / "batch"
    assert cli.main(["interoperability", "process-batch", "--output-dir", str(output)]) == 0
    assert cli.main(["interoperability", "validate-fhir", "--input-dir", str(output / "fhir")]) == 0
    negative = tmp_path / "negative"
    assert cli.main(["interoperability", "generate-negative", "--output-dir", str(negative)]) == 0
    assert cli.main(["interoperability", "validate-hl7", "--input-dir", str(negative / "hl7")]) == 1
    assert cli.main(["list-datasets"]) == 0
    assert "patients: schema 1.0.0" in capsys.readouterr().out


def test_config_and_snowflake_contract_align_with_existing_foundation() -> None:
    foundation = json.loads(Path("snowflake/config/foundation.json").read_text())
    contracts = json.loads(
        Path("snowflake/contracts/interoperability_raw_contracts.json").read_text()
    )
    available = {
        f"{database}.{schema}"
        for database, definition in foundation["databases"].items()
        for schema in definition["schemas"]
    }
    assert {contract["location"] for contract in contracts["contracts"]} <= available
    assert contracts["status"] == "STATIC_CONTRACT_NOT_DEPLOYED"


def test_configuration_rejects_non_synthetic_mode(tmp_path: Path) -> None:
    config = deepcopy(load_config())
    config["synthetic_flag"] = False
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="synthetic_flag"):
        load_config(path)
