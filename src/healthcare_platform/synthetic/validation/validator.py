"""Structural, referential, temporal and healthcare business validation."""

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Any

from healthcare_platform.synthetic import code_sets
from healthcare_platform.synthetic.generators.types import DatasetMap, Record
from healthcare_platform.synthetic.schemas import DATASET_ORDER, SCHEMAS
from healthcare_platform.synthetic.validation.report import ValidationIssue, ValidationReport


def _parse_value(value: str | None, data_type: str) -> Any:
    if value is None or value == "":
        return None
    if data_type == "boolean":
        return value.lower() == "true"
    if data_type == "integer":
        return int(value)
    if data_type == "number":
        return float(value)
    return value


def load_csv_datasets(input_dir: Path) -> DatasetMap:
    relational = input_dir / "relational"
    data: DatasetMap = {}
    for dataset in DATASET_ORDER:
        path = relational / f"{dataset}.csv"
        if not path.exists():
            raise ValueError(f"expected dataset file is missing: {path}")
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            expected = [field.name for field in SCHEMAS[dataset].fields]
            if reader.fieldnames != expected:
                raise ValueError(f"unexpected columns in {path}; expected {expected}")
            data[dataset] = [
                {
                    field.name: _parse_value(row[field.name], field.data_type)
                    for field in SCHEMAS[dataset].fields
                }
                for row in reader
            ]
    return data


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(data: DatasetMap, reference_date: date) -> ValidationReport:
    issues: list[ValidationIssue] = []

    def add(rule: str, dataset: str, record: Record, message: str) -> None:
        pk = SCHEMAS[dataset].primary_key[0]
        issues.append(ValidationIssue(rule, dataset, str(record.get(pk, "<missing>")), message))

    keys: dict[str, set[Any]] = {}
    for dataset in DATASET_ORDER:
        schema = SCHEMAS[dataset]
        rows = data.get(dataset, [])
        pk = schema.primary_key[0]
        values = [row.get(pk) for row in rows]
        keys[dataset] = {value for value in values if value is not None}
        if len(keys[dataset]) != len(values):
            issues.append(
                ValidationIssue(
                    "STRUCT-PK", dataset, "<dataset>", "primary key is null or duplicated"
                )
            )
        for row in rows:
            for field in schema.fields:
                value = row.get(field.name)
                if value is None and not field.nullable:
                    add("STRUCT-NULL", dataset, row, f"{field.name} is required")
                if (
                    value is not None
                    and field.controlled_code_set
                    and value not in code_sets.ALL_CODE_SETS[field.controlled_code_set]
                ):
                    add(
                        "STRUCT-CODE",
                        dataset,
                        row,
                        f"{field.name} has uncontrolled value {value!r}",
                    )
                if value is not None:
                    try:
                        if field.data_type == "date":
                            date.fromisoformat(str(value))
                        elif field.data_type == "datetime":
                            _dt(str(value))
                    except ValueError:
                        add(
                            "STRUCT-TYPE",
                            dataset,
                            row,
                            f"{field.name} is not a valid {field.data_type}",
                        )

    for dataset, schema in SCHEMAS.items():
        for row in data.get(dataset, []):
            for foreign_key in schema.foreign_keys:
                value = row.get(foreign_key.fields[0])
                if value is not None and value not in keys[foreign_key.reference_dataset]:
                    add("REF-FK", dataset, row, f"{foreign_key.fields[0]} does not resolve")

    patients = {row["patient_id"]: row for row in data["patients"]}
    for patient in data["patients"]:
        if patient["deceased_flag"] != bool(patient["death_date"]):
            add("BR-PAT-001", "patients", patient, "deceased_flag and death_date disagree")
        if patient["death_date"] and date.fromisoformat(
            patient["death_date"]
        ) <= date.fromisoformat(patient["birth_date"]):
            add("TIME-PAT-001", "patients", patient, "death_date must follow birth_date")
    for dataset, datetime_field in (
        ("encounters", "start_datetime"),
        ("appointments", "appointment_datetime"),
        ("clinical_events", "event_datetime"),
        ("pathology_results", "specimen_datetime"),
        ("medication_events", "event_datetime"),
    ):
        for row in data[dataset]:
            if _dt(row[datetime_field]).date() <= date.fromisoformat(
                patients[row["patient_id"]]["birth_date"]
            ):
                add("TIME-BIRTH-001", dataset, row, "clinical activity must follow birth_date")
    admissions_by_id = {row["admission_id"]: row for row in data["admissions"]}
    for row in data["admissions"]:
        if row["discharge_datetime"]:
            admission = _dt(row["admission_datetime"])
            discharge = _dt(row["discharge_datetime"])
            if discharge < admission:
                add("TIME-ADM-001", "admissions", row, "discharge precedes admission")
            if row["length_of_stay_days"] != (discharge.date() - admission.date()).days:
                add("BR-ADM-001", "admissions", row, "length_of_stay_days is inconsistent")
        if row["readmission_flag"] != bool(row["prior_admission_id"]):
            add("BR-ADM-002", "admissions", row, "readmission flag lacks matching prior admission")
        if row["prior_admission_id"]:
            prior = admissions_by_id.get(row["prior_admission_id"])
            if prior and _dt(prior["admission_datetime"]) > _dt(row["admission_datetime"]):
                add("TIME-ADM-002", "admissions", row, "prior admission starts after readmission")
    for row in data["appointments"]:
        if _dt(row["booking_datetime"]) > _dt(row["appointment_datetime"]):
            add("TIME-APT-001", "appointments", row, "booking follows appointment")
        cancelled = row["attendance_status"] == "CANCELLED"
        if cancelled != bool(row["cancellation_reason"]):
            add("BR-APT-001", "appointments", row, "cancellation reason does not align with status")
    for row in data["pathways"]:
        start = date.fromisoformat(row["clock_start_date"])
        end = (
            date.fromisoformat(row["completion_date"]) if row["completion_date"] else reference_date
        )
        if row["current_status"] == "COMPLETED" and not row["completion_date"]:
            add("BR-PTH-001", "pathways", row, "completed pathway has no completion_date")
        if end < start:
            add("TIME-PTH-001", "pathways", row, "completion precedes clock start")
        wait = (end - start).days
        if row["waiting_days"] != wait or row["breach_flag"] != (wait > 126):
            add("BR-PTH-002", "pathways", row, "waiting days or breach flag is inconsistent")
    for row in data["pathology_results"]:
        if _dt(row["result_datetime"]) < _dt(row["specimen_datetime"]):
            add("TIME-LAB-001", "pathology_results", row, "result precedes specimen")
        abnormal = (
            row["result_value"] < row["reference_low"]
            or row["result_value"] > row["reference_high"]
        )
        if row["abnormal_flag"] != abnormal:
            add("BR-LAB-001", "pathology_results", row, "abnormal flag disagrees with range")
    consent_by_patient = {row["patient_id"]: row for row in data["research_consent"]}
    for row in data["research_consent"]:
        if row["consent_status"] == "WITHDRAWN" and not row["withdrawal_date"]:
            add("BR-CON-001", "research_consent", row, "withdrawn consent lacks withdrawal_date")
        if row["withdrawal_date"] and date.fromisoformat(
            row["withdrawal_date"]
        ) < date.fromisoformat(row["valid_from"]):
            add("TIME-CON-001", "research_consent", row, "withdrawal precedes valid_from")
        expected = row["consent_status"] == "ACTIVE"
        if row["research_use_allowed"] != expected:
            add(
                "BR-CON-002", "research_consent", row, "research eligibility disagrees with consent"
            )
    for row in data["research_cohorts"]:
        consent = consent_by_patient.get(row["patient_id"])
        if not consent or not consent["research_use_allowed"] or not row["eligible_flag"]:
            add("BR-COH-001", "research_cohorts", row, "cohort member lacks eligible consent")

    return ValidationReport(
        valid=not issues,
        datasets_validated=len(DATASET_ORDER),
        rows_validated=sum(len(data[name]) for name in DATASET_ORDER),
        issues=tuple(issues),
    )
