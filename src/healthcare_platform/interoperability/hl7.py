"""Small deterministic HL7 v2.5 parser and generator; no MLLP transport."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from healthcare_platform.interoperability.contracts import ParsedPayload, ValidationIssue

SUPPORTED_SEGMENTS = {"MSH", "EVN", "PID", "PV1", "ORC", "OBR", "OBX", "SCH", "AIP", "NTE"}
REQUIRED_SEGMENTS = {
    "ADT^A01": {"MSH", "EVN", "PID", "PV1"},
    "ADT^A03": {"MSH", "EVN", "PID", "PV1"},
    "ADT^A08": {"MSH", "EVN", "PID", "PV1"},
    "ORM^O01": {"MSH", "PID", "PV1", "ORC", "OBR"},
    "ORU^R01": {"MSH", "PID", "PV1", "OBR", "OBX"},
    "SIU^S12": {"MSH", "SCH", "PID", "AIP"},
}


@dataclass(frozen=True)
class HL7Message:
    segments: tuple[tuple[str, ...], ...]
    field_separator: str
    component_separator: str

    def first(self, name: str) -> tuple[str, ...] | None:
        return next((segment for segment in self.segments if segment[0] == name), None)


def parse_message(text: str) -> HL7Message:
    lines = [line for line in text.replace("\r\n", "\r").replace("\n", "\r").split("\r") if line]
    if not lines or not lines[0].startswith("MSH"):
        return HL7Message(tuple(tuple(line.split("|")) for line in lines), "|", "^")
    if len(lines[0]) < 8:
        return HL7Message((tuple(lines[0].split("|")),), "|", "^")
    separator = lines[0][3]
    component = lines[0][4]
    return HL7Message(tuple(tuple(line.split(separator)) for line in lines), separator, component)


def component(field: str, position: int, separator: str = "^") -> str:
    parts = field.split(separator)
    return parts[position] if position < len(parts) else ""


def _field(segment: tuple[str, ...] | None, position: int) -> str:
    return segment[position] if segment is not None and position < len(segment) else ""


def validate_message(text: str, config: dict[str, Any]) -> ParsedPayload:
    message = parse_message(text)
    issues: list[ValidationIssue] = []
    if not message.segments or message.segments[0][0] != "MSH":
        issues.append(ValidationIssue("MISSING_MSH", "MSH must be the first segment"))
    if message.field_separator != "|":
        issues.append(ValidationIssue("INVALID_FIELD_SEPARATOR", "expected | field separator"))
    msh = message.first("MSH")
    message_type = _field(msh, 8)
    control_id = _field(msh, 9) or "UNKNOWN"
    timestamp = _field(msh, 6)
    version = _field(msh, 11)
    if msh is not None and message_type not in config["supported_hl7_messages"]:
        issues.append(
            ValidationIssue(
                "UNSUPPORTED_MESSAGE", f"unsupported message type {message_type or 'UNKNOWN'}"
            )
        )
    if msh is not None and version != config["supported_hl7_version"]:
        issues.append(
            ValidationIssue(
                "UNSUPPORTED_VERSION", f"unsupported HL7 version {version or 'UNKNOWN'}"
            )
        )
    if control_id == "UNKNOWN":
        issues.append(ValidationIssue("MISSING_CONTROL_ID", "MSH-10 is required"))
    try:
        datetime.strptime(timestamp, "%Y%m%d%H%M%S")
    except ValueError:
        issues.append(ValidationIssue("MALFORMED_TIMESTAMP", "MSH-7 must use YYYYMMDDHHMMSS"))
    present = {segment[0] for segment in message.segments}
    for name in sorted(REQUIRED_SEGMENTS.get(message_type, set()) - present):
        issues.append(
            ValidationIssue("MISSING_REQUIRED_SEGMENT", f"{name} is required for {message_type}")
        )
    for segment in message.segments:
        if segment[0] not in SUPPORTED_SEGMENTS:
            issues.append(
                ValidationIssue(
                    "UNMAPPED_SEGMENT", f"preserved unsupported segment {segment[0]}", "WARNING"
                )
            )
    pid = message.first("PID")
    patient_id = component(_field(pid, 3), 0) or None
    if message_type in REQUIRED_SEGMENTS and not patient_id:
        issues.append(ValidationIssue("MISSING_PATIENT_IDENTIFIER", "PID-3 is required"))
    pv1 = message.first("PV1")
    encounter_id = _field(pv1, 19) or None
    sch = message.first("SCH")
    appointment_id = _field(sch, 1) or None
    if message_type.startswith(("ADT", "ORM", "ORU")) and not encounter_id:
        issues.append(ValidationIssue("MISSING_ENCOUNTER_IDENTIFIER", "PV1-19 is required"))
    if message_type == "SIU^S12" and not appointment_id:
        issues.append(ValidationIssue("MISSING_APPOINTMENT_IDENTIFIER", "SCH-1 is required"))
    obr = message.first("OBR")
    obx = message.first("OBX")
    if message_type == "ORU^R01" and (
        not _field(obr, 3) or not _field(obx, 5) or not _field(obx, 6)
    ):
        issues.append(
            ValidationIssue("INVALID_ORDER_RESULT", "ORU requires result ID, value and unit")
        )
    source = _field(msh, 2)
    if not source.startswith("SYN-"):
        issues.append(
            ValidationIssue("MISSING_SYNTHETIC_MARKER", "sending application must begin SYN-")
        )
    mapped = {
        "message_control_id": control_id,
        "message_type": message_type,
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "appointment_id": appointment_id,
        "provider_id": component(_field(message.first("AIP"), 3), 0) or _field(pv1, 7) or None,
        "order_id": _field(obr, 3) or _field(message.first("ORC"), 2),
        "result_value": _field(obx, 5),
        "result_unit": _field(obx, 6),
    }
    preserved = {segment[0]: list(segment[1:]) for segment in message.segments}
    unmapped = {
        segment[0]: list(segment[1:])
        for segment in message.segments
        if segment[0] not in REQUIRED_SEGMENTS.get(message_type, set())
    }
    event_timestamp = (
        datetime.strptime(timestamp, "%Y%m%d%H%M%S").strftime("%Y-%m-%dT%H:%M:%SZ")
        if timestamp.isdigit() and len(timestamp) == 14
        else ""
    )
    return ParsedPayload(
        "HL7V2",
        message_type or "UNKNOWN",
        control_id,
        patient_id,
        encounter_id,
        event_timestamp,
        mapped,
        preserved,
        unmapped,
        (),
        tuple(issues),
    )


def _msh(message_type: str, control_id: str, timestamp: str, config: dict[str, Any]) -> str:
    return "|".join(
        [
            "MSH",
            "^~\\&",
            config["source_systems"]["hl7"],
            "SYN-FACILITY",
            "HEDP-RAW",
            "HEDP",
            timestamp,
            "",
            message_type,
            control_id,
            "T",
            config["supported_hl7_version"],
        ]
    )


def generate_messages(
    data: dict[str, list[dict[str, Any]]], config: dict[str, Any]
) -> list[tuple[str, str]]:
    patient = data["patients"][0]
    encounter = data["encounters"][0]
    pathology = data["pathology_results"][0]
    appointment = data["appointments"][0]
    appointment_time = appointment["appointment_datetime"].replace("-", "").replace(":", "")
    timestamp = config["reference_date"].replace("-", "") + "120000"
    birth_date = patient["birth_date"].replace("-", "")
    pid = (
        f"PID|1||{patient['patient_id']}^^^HEDP^PI||SYNTHETIC^PATIENT||"
        f"{birth_date}|{patient['sex'][0]}"
    )
    pv1 = (
        f"PV1|1|O|{encounter['location_id']}||||{encounter['provider_id']}"
        f"||||||||||||{encounter['encounter_id']}"
    )
    messages: list[tuple[str, str]] = []
    for index, event in enumerate(("ADT^A01", "ADT^A03", "ADT^A08"), start=1):
        control = f"HL7-ADT-{index:03d}"
        text = (
            "\r".join(
                [
                    _msh(event, control, timestamp, config),
                    f"EVN|{event.split('^')[1]}|{timestamp}",
                    pid,
                    pv1,
                ]
            )
            + "\r"
        )
        messages.append((control, text))
    orm_id = "HL7-ORM-001"
    messages.append(
        (
            orm_id,
            "\r".join(
                [
                    _msh("ORM^O01", orm_id, timestamp, config),
                    pid,
                    pv1,
                    f"ORC|NW|{pathology['pathology_result_id']}",
                    f"OBR|1|{pathology['pathology_result_id']}|{pathology['pathology_result_id']}|{pathology['test_code']}^{pathology['test_name']}",
                ]
            )
            + "\r",
        )
    )
    oru_id = "HL7-ORU-001"
    messages.append(
        (
            oru_id,
            "\r".join(
                [
                    _msh("ORU^R01", oru_id, timestamp, config),
                    pid,
                    pv1,
                    f"OBR|1|{pathology['pathology_result_id']}|{pathology['pathology_result_id']}|{pathology['test_code']}^{pathology['test_name']}",
                    f"OBX|1|NM|{pathology['test_code']}||{pathology['result_value']}|{pathology['result_unit']}|||||{pathology['status']}",
                ]
            )
            + "\r",
        )
    )
    siu_id = "HL7-SIU-001"
    messages.append(
        (
            siu_id,
            "\r".join(
                [
                    _msh("SIU^S12", siu_id, timestamp, config),
                    (f"SCH|{appointment['appointment_id']}|||||||||||{appointment_time[:14]}"),
                    pid,
                    f"AIP|1||{appointment['provider_id']}^SYNTHETIC PROVIDER",
                ]
            )
            + "\r",
        )
    )
    return messages
