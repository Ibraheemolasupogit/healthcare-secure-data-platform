"""Typed source-neutral ingestion and validation contracts."""

from dataclasses import asdict, dataclass
from typing import Any, Literal

ValidationLevel = Literal["ERROR", "WARNING"]
ValidationStatus = Literal["ACCEPTED", "ACCEPTED_WITH_WARNINGS", "REJECTED", "UNSUPPORTED"]


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    level: ValidationLevel = "ERROR"

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ParsedPayload:
    source_format: str
    message_type: str
    record_id: str
    patient_id: str | None
    encounter_id: str | None
    event_timestamp: str
    mapped_fields: dict[str, Any]
    preserved_fields: dict[str, Any]
    unmapped_fields: dict[str, Any]
    references: tuple[str, ...]
    issues: tuple[ValidationIssue, ...]

    @property
    def status(self) -> ValidationStatus:
        errors = [issue for issue in self.issues if issue.level == "ERROR"]
        warnings = [issue for issue in self.issues if issue.level == "WARNING"]
        if any(issue.code.startswith("UNSUPPORTED") for issue in errors):
            return "UNSUPPORTED"
        if errors:
            return "REJECTED"
        return "ACCEPTED_WITH_WARNINGS" if warnings else "ACCEPTED"


@dataclass(frozen=True)
class IngestionEnvelope:
    ingestion_id: str
    source_format: str
    source_system: str
    source_message_type: str
    source_record_id: str
    source_patient_id: str | None
    canonical_patient_id: str | None
    source_encounter_id: str | None
    canonical_encounter_id: str | None
    event_timestamp: str
    received_timestamp: str
    payload_version: str
    schema_version: str
    parser_version: str
    validation_status: ValidationStatus
    validation_error_count: int
    warning_count: int
    payload_checksum: str
    correlation_id: str
    batch_id: str
    quarantine_flag: bool
    raw_payload_path: str
    canonical_mapping_status: str
    environment: str
    synthetic_flag: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QuarantineRecord:
    quarantine_id: str
    source_format: str
    source_message_type: str
    source_record_id: str
    validation_errors: tuple[str, ...]
    warning_details: tuple[str, ...]
    payload_checksum: str
    raw_payload_path: str
    detected_at: str
    parser_version: str
    schema_version: str
    retry_eligible: bool
    disposition: str
    synthetic_flag: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
