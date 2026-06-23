"""Deterministic local interoperability batch processing."""

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from healthcare_platform.interoperability.config import DEFAULT_CONFIG_PATH, load_config
from healthcare_platform.interoperability.contracts import (
    IngestionEnvelope,
    ParsedPayload,
    QuarantineRecord,
    ValidationIssue,
)
from healthcare_platform.interoperability.fhir import (
    generate_resources,
    parse_resource,
    validate_bundle,
)
from healthcare_platform.interoperability.hl7 import generate_messages, validate_message
from healthcare_platform.interoperability.identifiers import (
    CrosswalkEntry,
    build_crosswalk,
    ingestion_id,
    stable_digest,
)
from healthcare_platform.synthetic.schemas import DATASET_ORDER

DEFAULT_CANONICAL_INPUT = Path("data/samples/small/relational")


def checksum_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _prepare_output(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise ValueError(f"output directory is not empty: {path}; pass --overwrite")
    if path.exists() and overwrite:
        for item in sorted(path.rglob("*"), reverse=True):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                item.rmdir()
    path.mkdir(parents=True, exist_ok=True)


def load_canonical(input_dir: Path = DEFAULT_CANONICAL_INPUT) -> dict[str, list[dict[str, Any]]]:
    data: dict[str, list[dict[str, Any]]] = {}
    for dataset in DATASET_ORDER:
        path = input_dir / f"{dataset}.csv"
        if not path.exists():
            raise ValueError(f"canonical input is missing: {path}")
        with path.open(encoding="utf-8", newline="") as handle:
            data[dataset] = list(csv.DictReader(handle))
    return data


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def generate_fhir(
    input_dir: Path,
    output_dir: Path,
    config_path: Path = DEFAULT_CONFIG_PATH,
    overwrite: bool = False,
) -> tuple[Path, ...]:
    config = load_config(config_path)
    _prepare_output(output_dir, overwrite)
    resources = generate_resources(load_canonical(input_dir), config)
    resource_paths: list[Path] = []
    for resource in resources:
        path = output_dir / "resources" / f"{resource['resourceType']}-{resource['id']}.json"
        _json(path, resource)
        resource_paths.append(path)
    entries: list[dict[str, Any]] = [
        {"fullUrl": f"urn:uuid:{item['resourceType']}-{item['id']}", "resource": item}
        for item in resources
    ]
    for bundle_type in ("collection", "transaction", "batch"):
        bundle_entries = entries
        if bundle_type != "collection":
            bundle_entries = [
                {**entry, "request": {"method": "POST", "url": entry["resource"]["resourceType"]}}
                for entry in entries
            ]
        bundle = {
            "resourceType": "Bundle",
            "id": f"BND-{bundle_type.upper()}-001",
            "type": bundle_type,
            "timestamp": config["reference_date"] + "T12:00:00Z",
            "meta": {"tag": [{"code": "SYNTHETIC-NON-TRANSACTIONAL-EXAMPLE"}]},
            "disclaimer": (
                "FHIR-inspired synthetic bundle; not formally conformant or live "
                "transaction support."
            ),
            "entry": bundle_entries,
        }
        path = output_dir / "bundles" / f"{bundle_type}.json"
        _json(path, bundle)
        resource_paths.append(path)
    return tuple(resource_paths)


def generate_hl7(
    input_dir: Path,
    output_dir: Path,
    config_path: Path = DEFAULT_CONFIG_PATH,
    overwrite: bool = False,
) -> tuple[Path, ...]:
    config = load_config(config_path)
    _prepare_output(output_dir, overwrite)
    paths: list[Path] = []
    for control_id, message in generate_messages(load_canonical(input_dir), config):
        path = output_dir / "messages" / f"{control_id}.hl7"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(message, encoding="utf-8", newline="")
        paths.append(path)
    return tuple(paths)


def _report(parsed: list[ParsedPayload]) -> dict[str, Any]:
    counts = {
        status: sum(item.status == status for item in parsed)
        for status in ("ACCEPTED", "ACCEPTED_WITH_WARNINGS", "REJECTED", "UNSUPPORTED")
    }
    return {
        "schema_version": "1.0.0",
        "valid": not any(item.status in {"REJECTED", "UNSUPPORTED"} for item in parsed),
        "payload_count": len(parsed),
        "counts": counts,
        "results": [
            {
                "source_format": item.source_format,
                "message_type": item.message_type,
                "record_id": item.record_id,
                "status": item.status,
                "mapped_fields": item.mapped_fields,
                "preserved_fields": item.preserved_fields,
                "unmapped_fields": item.unmapped_fields,
                "references": item.references,
                "issues": [issue.as_dict() for issue in item.issues],
            }
            for item in parsed
        ],
    }


def _write_report(output_dir: Path, report: dict[str, Any], label: str) -> None:
    _json(output_dir / f"{label}_validation_report.json", report)
    counts = report["counts"]
    markdown = [
        f"# {label.upper()} validation report",
        "",
        f"- Result: **{'PASS' if report['valid'] else 'FAIL'}**",
        f"- Payloads: {report['payload_count']}",
        f"- Accepted: {counts['ACCEPTED']}",
        f"- Accepted with warnings: {counts['ACCEPTED_WITH_WARNINGS']}",
        f"- Rejected: {counts['REJECTED']}",
        f"- Unsupported: {counts['UNSUPPORTED']}",
        "",
        "This is simplified portfolio validation, not formal standards conformance.",
        "",
    ]
    (output_dir / f"{label}_validation_report.md").write_text("\n".join(markdown), encoding="utf-8")


def validate_corpus(
    input_dir: Path,
    source_format: str,
    config_path: Path = DEFAULT_CONFIG_PATH,
    report_dir: Path | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    parsed: list[ParsedPayload] = []
    if source_format == "FHIR":
        bundle_paths = sorted((input_dir / "bundles").glob("*.json"))
        if bundle_paths:
            for path in bundle_paths:
                parsed.extend(validate_bundle(json.loads(path.read_text(encoding="utf-8")), config))
        else:
            entries: list[dict[str, Any]] = []
            for path in sorted(input_dir.rglob("*.json")):
                try:
                    entries.append({"resource": json.loads(path.read_text(encoding="utf-8"))})
                except json.JSONDecodeError:
                    parsed.append(parse_resource(path.read_text(encoding="utf-8"), config))
            parsed.extend(validate_bundle({"entry": entries}, config))
    elif source_format == "HL7V2":
        seen: set[str] = set()
        for path in sorted(input_dir.rglob("*.hl7")):
            item = validate_message(path.read_text(encoding="utf-8"), config)
            if item.record_id in seen and item.record_id != "UNKNOWN":
                duplicate_issue = item.issues + (
                    ValidationIssue(
                        "DUPLICATE_CONTROL_ID", f"duplicate control ID {item.record_id}"
                    ),
                )
                item = ParsedPayload(**{**item.__dict__, "issues": duplicate_issue})
            seen.add(item.record_id)
            parsed.append(item)
    else:
        raise ValueError("source_format must be FHIR or HL7V2")
    report = _report(parsed)
    if report_dir:
        report_dir.mkdir(parents=True, exist_ok=True)
        _write_report(report_dir, report, source_format.lower())
    return report


def _envelope(
    item: ParsedPayload,
    raw: bytes,
    raw_path: str,
    config: dict[str, Any],
    batch_id: str,
) -> IngestionEnvelope:
    errors = [issue for issue in item.issues if issue.level == "ERROR"]
    warnings = [issue for issue in item.issues if issue.level == "WARNING"]
    checksum = checksum_bytes(raw)
    return IngestionEnvelope(
        ingestion_id(batch_id, item.source_format, item.record_id),
        item.source_format,
        config["source_systems"]["fhir" if item.source_format == "FHIR" else "hl7"],
        item.message_type,
        item.record_id,
        item.patient_id,
        item.patient_id,
        item.encounter_id,
        item.encounter_id,
        item.event_timestamp or config["reference_date"] + "T00:00:00Z",
        config["reference_date"] + "T12:00:00Z",
        config["supported_hl7_version"] if item.source_format == "HL7V2" else "FHIR-INSPIRED-1",
        config["schema_version"],
        config["parser_version"],
        item.status,
        len(errors),
        len(warnings),
        checksum,
        f"COR-{stable_digest(batch_id, item.record_id)}",
        batch_id,
        item.status in {"REJECTED", "UNSUPPORTED"},
        raw_path,
        "MAPPED" if item.patient_id or item.encounter_id else "NOT_APPLICABLE",
        config["environment"],
        True,
    )


def process_batch(
    input_dir: Path = DEFAULT_CANONICAL_INPUT,
    output_dir: Path = Path("data/samples/interoperability"),
    config_path: Path = DEFAULT_CONFIG_PATH,
    seed: int = 42,
    overwrite: bool = False,
) -> dict[str, Any]:
    config = load_config(config_path)
    _prepare_output(output_dir, overwrite)
    batch_id = f"BAT-{stable_digest(str(seed), config['reference_date'], config['schema_version'])}"
    fhir_dir = output_dir / "fhir"
    hl7_dir = output_dir / "hl7"
    generate_fhir(input_dir, fhir_dir, config_path, overwrite=True)
    generate_hl7(input_dir, hl7_dir, config_path, overwrite=True)
    fhir_bundle = json.loads((fhir_dir / "bundles/collection.json").read_text(encoding="utf-8"))
    parsed_with_raw: list[tuple[ParsedPayload, bytes, str]] = []
    for entry in fhir_bundle["entry"]:
        resource = entry["resource"]
        resource_relative_path = f"fhir/resources/{resource['resourceType']}-{resource['id']}.json"
        raw = (output_dir / resource_relative_path).read_bytes()
        parsed_with_raw.append(
            (
                parse_resource(resource, config),
                raw,
                resource_relative_path,
            )
        )
    for path in sorted((hl7_dir / "messages").glob("*.hl7")):
        raw = path.read_bytes()
        parsed_with_raw.append(
            (validate_message(raw.decode(), config), raw, path.relative_to(output_dir).as_posix())
        )
    envelopes = [
        _envelope(item, raw, path, config, batch_id) for item, raw, path in parsed_with_raw
    ]
    crosswalk_entries: list[CrosswalkEntry] = []
    for envelope in envelopes:
        for identifier_type, source_id, canonical_id in (
            ("PATIENT", envelope.source_patient_id, envelope.canonical_patient_id),
            ("ENCOUNTER", envelope.source_encounter_id, envelope.canonical_encounter_id),
        ):
            if source_id and canonical_id:
                crosswalk_entries.append(
                    CrosswalkEntry(
                        envelope.source_format,
                        envelope.source_system,
                        identifier_type,
                        source_id,
                        canonical_id,
                    )
                )
        if envelope.source_record_id.startswith(("ORG-", "PRV-", "APT-", "LAB-")):
            identifier_type = {
                "ORG": "ORGANISATION",
                "PRV": "PROVIDER",
                "APT": "APPOINTMENT",
                "LAB": "PATHOLOGY_RESULT",
            }[envelope.source_record_id[:3]]
            crosswalk_entries.append(
                CrosswalkEntry(
                    envelope.source_format,
                    envelope.source_system,
                    identifier_type,
                    envelope.source_record_id,
                    envelope.source_record_id,
                )
            )
    for item, _, _ in parsed_with_raw:
        for identifier_type, source_id in (
            ("APPOINTMENT", item.mapped_fields.get("appointment_id")),
            ("PROVIDER", item.mapped_fields.get("provider_id")),
            ("PATHOLOGY_RESULT", item.mapped_fields.get("order_id")),
        ):
            if isinstance(source_id, str) and source_id.startswith(("APT-", "PRV-", "LAB-")):
                crosswalk_entries.append(
                    CrosswalkEntry(
                        item.source_format,
                        config["source_systems"]["hl7"],
                        identifier_type,
                        source_id,
                        source_id,
                    )
                )
    crosswalk = build_crosswalk(crosswalk_entries)
    quarantine: list[QuarantineRecord] = []
    for item, raw, raw_path in parsed_with_raw:
        if item.status in {"REJECTED", "UNSUPPORTED"}:
            errors = tuple(issue.code for issue in item.issues if issue.level == "ERROR")
            warnings = tuple(issue.code for issue in item.issues if issue.level == "WARNING")
            quarantine.append(
                QuarantineRecord(
                    f"QUA-{stable_digest(batch_id, item.record_id)}",
                    item.source_format,
                    item.message_type,
                    item.record_id,
                    errors,
                    warnings,
                    checksum_bytes(raw),
                    raw_path,
                    config["reference_date"] + "T12:00:00Z",
                    config["parser_version"],
                    config["schema_version"],
                    bool(set(errors) & set(config["quarantine_retry_error_codes"])),
                    "REVIEW",
                    True,
                )
            )
    _json(output_dir / "canonical/ingestion_envelopes.json", [item.as_dict() for item in envelopes])
    _json(output_dir / "crosswalks/identifier_crosswalk.json", crosswalk)
    _json(
        output_dir / "quarantine/quarantine_records.json", [item.as_dict() for item in quarantine]
    )
    fhir_report = _report([item for item, _, _ in parsed_with_raw if item.source_format == "FHIR"])
    hl7_report = _report([item for item, _, _ in parsed_with_raw if item.source_format == "HL7V2"])
    _write_report(fhir_dir / "validation", fhir_report, "fhir")
    _write_report(hl7_dir / "validation", hl7_report, "hl7")
    payload_files = sorted(path for path in output_dir.rglob("*") if path.is_file())
    output_checksums = {
        path.relative_to(output_dir).as_posix(): checksum_bytes(path.read_bytes())
        for path in payload_files
    }
    manifest = {
        "batch_id": batch_id,
        "source_format": "FHIR_AND_HL7V2",
        "source_system": "SYNTHETIC_INTEROPERABILITY",
        "parser_version": config["parser_version"],
        "schema_version": config["schema_version"],
        "generation_seed": seed,
        "reference_date": config["reference_date"],
        "input_file_count": len(parsed_with_raw),
        "accepted_count": sum(item.validation_status == "ACCEPTED" for item in envelopes),
        "warning_count": sum(item.warning_count for item in envelopes),
        "rejected_count": sum(
            item.validation_status in {"REJECTED", "UNSUPPORTED"} for item in envelopes
        ),
        "duplicate_count": 0,
        "quarantine_count": len(quarantine),
        "crosswalk_count": len(crosswalk),
        "payload_checksums": {
            envelope.raw_payload_path: envelope.payload_checksum for envelope in envelopes
        },
        "output_checksums": output_checksums,
        "started_at": config["reference_date"] + "T12:00:00Z",
        "completed_at": config["reference_date"] + "T12:00:00Z",
        "runtime_duration_seconds": 0,
        "environment": config["environment"],
        "synthetic_flag": True,
        "git_commit": "NOT_CAPTURED_DETERMINISTIC_SAMPLE",
    }
    _json(output_dir / "manifests/ingestion_manifest.json", manifest)
    checksum_lines = [f"{digest}  {path}" for path, digest in sorted(output_checksums.items())]
    (output_dir / "manifests/checksums.sha256").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8"
    )
    return manifest


def generate_negative_corpus(output_dir: Path, overwrite: bool = False) -> None:
    _prepare_output(output_dir, overwrite)
    fhir_cases = {
        "missing-resource-type.json": {
            "id": "PAT-NEG-001",
            "meta": {"tag": [{"code": "SYNTHETIC-FHIR-INSPIRED"}]},
        },
        "unsupported-resource.json": {
            "resourceType": "ImagingStudy",
            "id": "IMG-NEG-001",
            "meta": {"tag": [{"code": "SYNTHETIC-FHIR-INSPIRED"}]},
        },
        "malformed-date.json": {
            "resourceType": "Patient",
            "id": "PAT-000000001",
            "birthDate": "not-a-date",
            "meta": {"tag": [{"code": "SYNTHETIC-FHIR-INSPIRED"}]},
        },
        "unresolved-reference.json": {
            "resourceType": "Encounter",
            "id": "ENC-000000001",
            "status": "finished",
            "subject": {"reference": "Patient/PAT-999999999"},
            "meta": {"tag": [{"code": "SYNTHETIC-FHIR-INSPIRED"}]},
        },
    }
    for name, payload in fhir_cases.items():
        _json(output_dir / "fhir" / name, payload)
    msh_prefix = "MSH|^~\\&|SYN-EPR|SYN-FACILITY|HEDP|HEDP|"
    hl7_cases = {
        "missing-msh.hl7": "PID|1||PAT-000000001^^^HEDP^PI\r",
        "unsupported-message.hl7": (
            msh_prefix + "20250101120000||MDM^T02|HL7-NEG-001|T|2.5\rPID|1||PAT-000000001\r"
        ),
        "missing-pid.hl7": (
            msh_prefix
            + "20250101120000||ADT^A01|HL7-NEG-002|T|2.5\r"
            + "EVN|A01|20250101120000\rPV1|1|O|||||||||||||||||ENC-000000001\r"
        ),
        "malformed-timestamp.hl7": (
            msh_prefix
            + "BADTIME||ADT^A08|HL7-NEG-003|T|2.5\rEVN|A08|BADTIME\r"
            + "PID|1||PAT-000000001\rPV1|1|O|||||||||||||||||ENC-000000001\r"
        ),
    }
    for name, hl7_payload in hl7_cases.items():
        path = output_dir / "hl7" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(hl7_payload, encoding="utf-8", newline="")
    _json(
        output_dir / "expected_errors.json",
        {
            "fhir": {
                "missing-resource-type.json": ["MISSING_RESOURCE_TYPE", "MISSING_REQUIRED_FIELD"],
                "unsupported-resource.json": ["UNSUPPORTED_RESOURCE"],
                "malformed-date.json": ["MALFORMED_DATE"],
                "unresolved-reference.json": ["UNRESOLVED_REFERENCE"],
            },
            "hl7": {
                "missing-msh.hl7": ["MISSING_MSH"],
                "unsupported-message.hl7": ["UNSUPPORTED_MESSAGE"],
                "missing-pid.hl7": ["MISSING_REQUIRED_SEGMENT", "MISSING_PATIENT_IDENTIFIER"],
                "malformed-timestamp.hl7": ["MALFORMED_TIMESTAMP"],
            },
        },
    )
    config = load_config()
    quarantined: list[dict[str, Any]] = []
    for source_format, directory, pattern in (
        ("FHIR", output_dir / "fhir", "*.json"),
        ("HL7V2", output_dir / "hl7", "*.hl7"),
    ):
        report = validate_corpus(directory, source_format)
        paths = sorted(directory.glob(pattern))
        for result, raw_path in zip(report["results"], paths, strict=True):
            error_codes = tuple(
                issue["code"] for issue in result["issues"] if issue["level"] == "ERROR"
            )
            warning_codes = tuple(
                issue["code"] for issue in result["issues"] if issue["level"] == "WARNING"
            )
            raw = raw_path.read_bytes()
            record = QuarantineRecord(
                f"QUA-{stable_digest(source_format, raw_path.name)}",
                source_format,
                result["message_type"],
                result["record_id"],
                error_codes,
                warning_codes,
                checksum_bytes(raw),
                raw_path.relative_to(output_dir).as_posix(),
                config["reference_date"] + "T12:00:00Z",
                config["parser_version"],
                config["schema_version"],
                bool(set(error_codes) & set(config["quarantine_retry_error_codes"])),
                result["status"],
                True,
            )
            quarantined.append(record.as_dict())
    _json(output_dir / "quarantine/quarantine_records.json", quarantined)


def describe_contracts() -> dict[str, Any]:
    value: dict[str, Any] = json.loads(
        Path("snowflake/contracts/interoperability_raw_contracts.json").read_text(encoding="utf-8")
    )
    return value
