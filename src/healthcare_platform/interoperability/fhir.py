"""Focused FHIR-inspired generation, parsing and validation."""

import json
from datetime import datetime
from typing import Any

from healthcare_platform.interoperability.contracts import ParsedPayload, ValidationIssue
from healthcare_platform.interoperability.terminology import map_code

CORE_FIELDS = {"resourceType", "id", "meta"}
STATUS_FIELDS = {
    "Encounter": {"planned", "in-progress", "finished", "cancelled"},
    "Appointment": {"booked", "fulfilled", "cancelled", "noshow"},
    "Observation": {"registered", "preliminary", "final", "amended"},
    "DiagnosticReport": {"registered", "preliminary", "final", "amended"},
    "MedicationRequest": {"active", "completed", "cancelled"},
    "Consent": {"active", "inactive", "rejected"},
}
REFERENCE_KEYS = {
    "subject",
    "encounter",
    "organization",
    "managingOrganization",
    "serviceProvider",
    "actor",
}


def metadata(source_system: str, schema_version: str) -> dict[str, Any]:
    return {
        "profile": [f"urn:hedp:fhir-inspired:{schema_version}"],
        "source": source_system,
        "tag": [{"system": "urn:hedp:provenance", "code": "SYNTHETIC-FHIR-INSPIRED"}],
    }


def identifier(system: str, value: str) -> list[dict[str, str]]:
    return [{"system": system, "value": value}]


def generate_resources(
    data: dict[str, list[dict[str, Any]]], config: dict[str, Any]
) -> list[dict[str, Any]]:
    """Map a small selection of existing canonical records into source-format views."""
    meta = metadata(config["source_systems"]["fhir"], config["schema_version"])
    ns = config["identifier_namespaces"]
    patients = data["patients"][:3]
    patient_ids = {row["patient_id"] for row in patients}
    encounters = [row for row in data["encounters"] if row["patient_id"] in patient_ids][:3]
    encounter_ids = {row["encounter_id"] for row in encounters}
    resources: list[dict[str, Any]] = []
    org = data["organisations"][0]
    location = next(
        row for row in data["locations"] if row["organisation_id"] == org["organisation_id"]
    )
    provider = next(
        row for row in data["providers"] if row["organisation_id"] == org["organisation_id"]
    )
    resources.extend(
        [
            {
                "resourceType": "Organization",
                "id": org["organisation_id"],
                "meta": meta,
                "identifier": identifier(ns["organisation"], org["organisation_id"]),
                "name": org["organisation_name"],
                "active": org["active_flag"],
            },
            {
                "resourceType": "Location",
                "id": location["location_id"],
                "meta": meta,
                "identifier": identifier("urn:hedp:synthetic:location", location["location_id"]),
                "status": "active" if location["active_flag"] else "inactive",
                "managingOrganization": {"reference": f"Organization/{org['organisation_id']}"},
            },
            {
                "resourceType": "Practitioner",
                "id": provider["provider_id"],
                "meta": meta,
                "identifier": identifier(ns["provider"], provider["provider_id"]),
                "active": provider["active_flag"],
                "extension": [
                    {"url": "urn:hedp:provider-role", "valueCode": provider["provider_role"]}
                ],
            },
        ]
    )
    referenced_organisations = {row["registered_gp_organisation_id"] for row in patients} | {
        row["organisation_id"] for row in encounters
    }
    for row in data["organisations"]:
        if row["organisation_id"] in referenced_organisations - {org["organisation_id"]}:
            resources.append(
                {
                    "resourceType": "Organization",
                    "id": row["organisation_id"],
                    "meta": meta,
                    "identifier": identifier(ns["organisation"], row["organisation_id"]),
                    "name": row["organisation_name"],
                    "active": row["active_flag"],
                }
            )
    for row in patients:
        resources.append(
            {
                "resourceType": "Patient",
                "id": row["patient_id"],
                "meta": meta,
                "identifier": identifier(ns["patient"], row["patient_id"]),
                "birthDate": row["birth_date"],
                "gender": map_code("sex", row["sex"])["target_code"],
                "managingOrganization": {
                    "reference": f"Organization/{row['registered_gp_organisation_id']}"
                },
            }
        )
    for row in encounters:
        resources.append(
            {
                "resourceType": "Encounter",
                "id": row["encounter_id"],
                "meta": meta,
                "identifier": identifier(ns["encounter"], row["encounter_id"]),
                "status": "finished" if row["status"] == "COMPLETED" else row["status"].lower(),
                "class": {"code": map_code("encounter_type", row["encounter_type"])["target_code"]},
                "subject": {"reference": f"Patient/{row['patient_id']}"},
                "serviceProvider": {"reference": f"Organization/{row['organisation_id']}"},
                "period": {"start": row["start_datetime"], "end": row["end_datetime"]},
            }
        )
    appointment = next(row for row in data["appointments"] if row["patient_id"] in patient_ids)
    appointment_provider = next(
        row for row in data["providers"] if row["provider_id"] == appointment["provider_id"]
    )
    if appointment_provider["provider_id"] != provider["provider_id"]:
        resources.append(
            {
                "resourceType": "Practitioner",
                "id": appointment_provider["provider_id"],
                "meta": meta,
                "identifier": identifier(ns["provider"], appointment_provider["provider_id"]),
                "active": appointment_provider["active_flag"],
                "extension": [
                    {
                        "url": "urn:hedp:provider-role",
                        "valueCode": appointment_provider["provider_role"],
                    }
                ],
            }
        )
    resources.append(
        {
            "resourceType": "Appointment",
            "id": appointment["appointment_id"],
            "meta": meta,
            "identifier": identifier(ns["appointment"], appointment["appointment_id"]),
            "status": {"ATTENDED": "fulfilled", "DID_NOT_ATTEND": "noshow"}.get(
                appointment["attendance_status"], appointment["attendance_status"].lower()
            ),
            "start": appointment["appointment_datetime"],
            "participant": [
                {"actor": {"reference": f"Patient/{appointment['patient_id']}"}},
                {"actor": {"reference": f"Practitioner/{appointment['provider_id']}"}},
            ],
        }
    )
    pathology = next(
        row for row in data["pathology_results"] if row["encounter_id"] in encounter_ids
    )
    observation_id = f"OBS-{pathology['pathology_result_id']}"
    resources.extend(
        [
            {
                "resourceType": "Observation",
                "id": observation_id,
                "meta": meta,
                "identifier": identifier(ns["pathology_result"], pathology["pathology_result_id"]),
                "status": {"CORRECTED": "amended"}.get(
                    pathology["status"], pathology["status"].lower()
                ),
                "subject": {"reference": f"Patient/{pathology['patient_id']}"},
                "encounter": {"reference": f"Encounter/{pathology['encounter_id']}"},
                "effectiveDateTime": pathology["result_datetime"],
                "code": {
                    "coding": [
                        {"system": "urn:hedp:synthetic:pathology", "code": pathology["test_code"]}
                    ]
                },
                "valueQuantity": {
                    "value": pathology["result_value"],
                    "unit": pathology["result_unit"],
                },
            },
            {
                "resourceType": "DiagnosticReport",
                "id": pathology["pathology_result_id"],
                "meta": meta,
                "identifier": identifier(ns["pathology_result"], pathology["pathology_result_id"]),
                "status": {"CORRECTED": "amended"}.get(
                    pathology["status"], pathology["status"].lower()
                ),
                "subject": {"reference": f"Patient/{pathology['patient_id']}"},
                "encounter": {"reference": f"Encounter/{pathology['encounter_id']}"},
                "effectiveDateTime": pathology["result_datetime"],
                "result": [{"reference": f"Observation/{observation_id}"}],
            },
        ]
    )
    medication = next(
        row for row in data["medication_events"] if row["encounter_id"] in encounter_ids
    )
    resources.append(
        {
            "resourceType": "MedicationRequest",
            "id": medication["medication_event_id"],
            "meta": meta,
            "identifier": identifier(
                "urn:hedp:synthetic:medication-event", medication["medication_event_id"]
            ),
            "status": "completed"
            if medication["status"] == "COMPLETED"
            else medication["status"].lower(),
            "intent": "order",
            "subject": {"reference": f"Patient/{medication['patient_id']}"},
            "encounter": {"reference": f"Encounter/{medication['encounter_id']}"},
            "authoredOn": medication["event_datetime"],
            "medicationCodeableConcept": {
                "coding": [
                    {
                        "system": "urn:hedp:synthetic:medication",
                        "code": medication["medication_code"],
                    }
                ]
            },
        }
    )
    consent = next(row for row in data["research_consent"] if row["patient_id"] in patient_ids)
    resources.append(
        {
            "resourceType": "Consent",
            "id": consent["consent_id"],
            "meta": meta,
            "identifier": identifier("urn:hedp:synthetic:consent", consent["consent_id"]),
            "status": {"ACTIVE": "active", "DECLINED": "rejected"}.get(
                consent["consent_status"], "inactive"
            ),
            "patient": {"reference": f"Patient/{consent['patient_id']}"},
            "dateTime": consent["updated_at"],
            "scope": {"text": "Synthetic research consent"},
        }
    )
    return resources


def _references(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        if isinstance(value.get("reference"), str):
            refs.append(value["reference"])
        for nested in value.values():
            refs.extend(_references(nested))
    elif isinstance(value, list):
        for nested in value:
            refs.extend(_references(nested))
    return refs


def parse_resource(raw: str | dict[str, Any], config: dict[str, Any]) -> ParsedPayload:
    issues: list[ValidationIssue] = []
    try:
        resource = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError as error:
        return ParsedPayload(
            "FHIR",
            "UNKNOWN",
            "UNKNOWN",
            None,
            None,
            "",
            {},
            {},
            {},
            (),
            (ValidationIssue("MALFORMED_JSON", str(error)),),
        )
    resource_type = resource.get("resourceType", "UNKNOWN")
    record_id = resource.get("id", "UNKNOWN")
    if resource_type == "UNKNOWN":
        issues.append(ValidationIssue("MISSING_RESOURCE_TYPE", "resourceType is required"))
    elif resource_type not in config["supported_fhir_resources"]:
        issues.append(
            ValidationIssue("UNSUPPORTED_RESOURCE", f"unsupported resourceType {resource_type}")
        )
    for field in CORE_FIELDS:
        if field not in resource:
            issues.append(ValidationIssue("MISSING_REQUIRED_FIELD", f"{field} is required"))
    if record_id != "UNKNOWN" and not any(
        record_id.startswith(prefix)
        for prefix in (
            "PAT-",
            "ORG-",
            "LOC-",
            "PRV-",
            "ENC-",
            "APT-",
            "OBS-",
            "LAB-",
            "MED-",
            "CON-",
        )
    ):
        issues.append(
            ValidationIssue(
                "NON_SYNTHETIC_IDENTIFIER", "id is not a recognised synthetic identifier"
            )
        )
    meta = resource.get("meta", {})
    if "SYNTHETIC-FHIR-INSPIRED" not in {tag.get("code") for tag in meta.get("tag", [])}:
        issues.append(
            ValidationIssue("MISSING_SYNTHETIC_MARKER", "synthetic provenance marker is required")
        )
    status = resource.get("status")
    accepted_statuses = config.get("accepted_status_codes", STATUS_FIELDS)
    if resource_type in accepted_statuses and status not in accepted_statuses[resource_type]:
        issues.append(ValidationIssue("INVALID_STATUS", f"invalid {resource_type} status"))
    for field in ("birthDate", "effectiveDateTime", "authoredOn", "dateTime", "start"):
        if field in resource:
            try:
                datetime.fromisoformat(str(resource[field]).replace("Z", "+00:00"))
            except ValueError:
                issues.append(ValidationIssue("MALFORMED_DATE", f"invalid {field}"))
    if "period" in resource:
        try:
            start = datetime.fromisoformat(resource["period"]["start"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(resource["period"]["end"].replace("Z", "+00:00"))
            if end < start:
                issues.append(ValidationIssue("INVALID_PERIOD", "period end precedes start"))
        except (KeyError, ValueError):
            issues.append(ValidationIssue("MALFORMED_DATE", "invalid period"))
    refs = tuple(sorted(set(_references(resource))))
    patient_ref = next((ref.split("/", 1)[1] for ref in refs if ref.startswith("Patient/")), None)
    encounter_ref = next(
        (ref.split("/", 1)[1] for ref in refs if ref.startswith("Encounter/")), None
    )
    mapped_keys = CORE_FIELDS | {
        "identifier",
        "status",
        "subject",
        "patient",
        "encounter",
        "period",
        "effectiveDateTime",
        "dateTime",
        "start",
    }
    return ParsedPayload(
        "FHIR",
        resource_type,
        record_id,
        patient_ref if resource_type != "Patient" else record_id,
        encounter_ref if resource_type != "Encounter" else record_id,
        str(
            resource.get("effectiveDateTime")
            or resource.get("dateTime")
            or resource.get("start")
            or resource.get("period", {}).get("start", config["reference_date"] + "T00:00:00Z")
        ),
        {key: resource[key] for key in resource.keys() & mapped_keys},
        {"extension": resource.get("extension", []), "raw": resource},
        {key: value for key, value in resource.items() if key not in mapped_keys},
        refs,
        tuple(issues),
    )


def validate_bundle(bundle: dict[str, Any], config: dict[str, Any]) -> list[ParsedPayload]:
    resources = [entry.get("resource", {}) for entry in bundle.get("entry", [])]
    parsed = [parse_resource(resource, config) for resource in resources]
    available = {f"{item.message_type}/{item.record_id}" for item in parsed}
    result: list[ParsedPayload] = []
    for item in parsed:
        unresolved = [ref for ref in item.references if ref not in available]
        issues = item.issues + tuple(
            ValidationIssue("UNRESOLVED_REFERENCE", f"reference does not resolve: {ref}")
            for ref in unresolved
        )
        result.append(ParsedPayload(**{**item.__dict__, "issues": issues}))
    return result
