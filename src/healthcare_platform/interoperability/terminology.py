"""Versioned portfolio terminology mappings; not authoritative clinical terminology."""

from typing import Any

from healthcare_platform.synthetic.code_sets import ALL_CODE_SETS

FHIR_SEX = {"FEMALE": "female", "MALE": "male", "INTERSEX": "other", "NOT_KNOWN": "unknown"}
ENCOUNTER_CLASS = {
    "EMERGENCY": "EMER",
    "INPATIENT": "IMP",
    "OUTPATIENT": "AMB",
    "COMMUNITY": "AMB",
    "VIRTUAL": "VR",
}


def map_code(code_set: str, source_code: str) -> dict[str, Any]:
    if code_set not in ALL_CODE_SETS:
        return {
            "source_code": source_code,
            "target_code": None,
            "mapping_status": "UNKNOWN_CODE_SET",
            "mapping_version": "1.0.0",
        }
    if source_code not in ALL_CODE_SETS[code_set]:
        return {
            "source_code": source_code,
            "target_code": None,
            "mapping_status": "UNKNOWN_CODE",
            "mapping_version": "1.0.0",
        }
    target = FHIR_SEX.get(source_code, ENCOUNTER_CLASS.get(source_code, source_code))
    return {
        "source_code": source_code,
        "target_code": target,
        "mapping_status": "MAPPED",
        "mapping_version": "1.0.0",
    }
