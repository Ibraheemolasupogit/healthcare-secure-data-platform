"""Structural, referential, temporal and healthcare business validation."""

import csv
from datetime import date, datetime
from decimal import Decimal
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


def _dec(value: Any) -> Decimal:
    return Decimal(str(value or "0"))


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

    # Milestone 7 billing/finance source validation. These are source-consistency checks, not
    # governed revenue recognition or payment-allocation transformations.
    if "billable_activity" in data:
        invoices = {row["invoice_id"]: row for row in data["invoices"]}
        invoice_lines_by_invoice: dict[str, list[Record]] = {}
        payments_by_invoice: dict[str, Decimal] = {}
        refunds_by_payment: dict[str, Decimal] = {}
        refunds_by_invoice: dict[str, Decimal] = {}
        adjustments_by_invoice: dict[str, Decimal] = {}

        for row in data["tariffs"]:
            if _dec(row["unit_price"]) < 0:
                add("FIN-TRF-001", "tariffs", row, "unit price must be non-negative")
            if row["valid_to"] and date.fromisoformat(row["valid_to"]) < date.fromisoformat(
                row["valid_from"]
            ):
                add("TIME-TRF-001", "tariffs", row, "tariff valid_to precedes valid_from")
        for row in data["contracts"]:
            if row["valid_to"] and date.fromisoformat(row["valid_to"]) < date.fromisoformat(
                row["valid_from"]
            ):
                add("TIME-CTR-001", "contracts", row, "contract valid_to precedes valid_from")
            if row["payment_terms_days"] <= 0:
                add("FIN-CTR-001", "contracts", row, "payment terms must be positive")
        for row in data["billable_activity"]:
            if _dec(row["quantity"]) <= 0:
                add("FIN-BACT-001", "billable_activity", row, "quantity must be positive")
            activity_date = _dt(row["activity_datetime"]).date()
            patient = patients[row["patient_id"]]
            if activity_date <= date.fromisoformat(patient["birth_date"]):
                add("TIME-BACT-001", "billable_activity", row, "activity must follow birth_date")
            if patient["death_date"] and activity_date > date.fromisoformat(patient["death_date"]):
                add("TIME-BACT-002", "billable_activity", row, "activity follows death_date")
            if (
                not row["encounter_id"]
                and not row["appointment_id"]
                and not row["clinical_event_id"]
            ):
                add("REF-BACT-001", "billable_activity", row, "activity lacks healthcare source")
        for row in data["claim_lines"]:
            expected = _dec(row["quantity"]) * _dec(row["unit_price"])
            if _dec(row["line_amount"]) != expected:
                add(
                    "FIN-CLML-001",
                    "claim_lines",
                    row,
                    "line amount does not equal quantity × price",
                )
            if row["line_status"] == "REJECTED" and not row["rejection_code"]:
                add("BR-CLML-001", "claim_lines", row, "rejected line lacks rejection code")
        claim_line_totals: dict[str, Decimal] = {}
        for row in data["claim_lines"]:
            claim_line_totals[row["claim_id"]] = claim_line_totals.get(
                row["claim_id"], Decimal("0")
            ) + _dec(row["line_amount"])
        for row in data["claims"]:
            if row["claim_status"] == "REJECTED" and not row["rejection_code"]:
                add("BR-CLM-001", "claims", row, "rejected claim lacks rejection code")
            if _dt(row["submitted_at"]).date() < date.fromisoformat(row["service_period_end"]):
                add("TIME-CLM-001", "claims", row, "claim submitted before service period end")
            if _dec(row["claimed_amount"]) != claim_line_totals.get(row["claim_id"], Decimal("0")):
                add("FIN-CLM-001", "claims", row, "claim amount does not equal claim lines")
        for row in data["invoice_lines"]:
            invoice_lines_by_invoice.setdefault(row["invoice_id"], []).append(row)
            net = _dec(row["quantity"]) * _dec(row["unit_price"])
            if _dec(row["net_amount"]) != net:
                add("FIN-INVL-001", "invoice_lines", row, "net does not equal quantity × price")
            if _dec(row["gross_amount"]) != _dec(row["net_amount"]) + _dec(row["tax_amount"]):
                add("FIN-INVL-002", "invoice_lines", row, "gross does not equal net plus tax")
        for row in data["invoices"]:
            if date.fromisoformat(row["due_date"]) < date.fromisoformat(row["invoice_date"]):
                add("TIME-INV-001", "invoices", row, "due date precedes invoice date")
            lines = invoice_lines_by_invoice.get(row["invoice_id"], [])
            if not lines:
                add("FIN-INV-001", "invoices", row, "invoice has no lines")
            subtotal = sum((_dec(line["net_amount"]) for line in lines), Decimal("0"))
            tax = sum((_dec(line["tax_amount"]) for line in lines), Decimal("0"))
            gross = sum((_dec(line["gross_amount"]) for line in lines), Decimal("0"))
            if (
                _dec(row["subtotal_amount"]) != subtotal
                or _dec(row["tax_amount"]) != tax
                or _dec(row["total_amount"]) != gross
            ):
                add("FIN-INV-002", "invoices", row, "invoice totals do not equal lines")
        attempts = {row["payment_attempt_id"]: row for row in data["payment_attempts"]}
        for row in data["payment_attempts"]:
            if row["attempt_status"] == "FAILED" and not row["failure_code"]:
                add("BR-PATM-001", "payment_attempts", row, "failed attempt lacks failure code")
            if row["attempt_status"] == "SUCCESS" and row["failure_code"]:
                add("BR-PATM-002", "payment_attempts", row, "successful attempt has failure code")
            invoice = invoices[row["invoice_id"]]
            if _dt(row["attempt_datetime"]).date() < date.fromisoformat(invoice["invoice_date"]):
                add("TIME-PATM-001", "payment_attempts", row, "attempt precedes invoice")
        for row in data["payments"]:
            attempt = attempts[row["payment_attempt_id"]]
            invoice = invoices[row["invoice_id"]]
            if attempt["attempt_status"] != "SUCCESS":
                add("REF-PAY-001", "payments", row, "payment does not reference successful attempt")
            if _dec(row["amount"]) <= 0:
                add("FIN-PAY-001", "payments", row, "payment amount must be positive")
            if row["currency"] != invoice["currency"]:
                add("FIN-PAY-002", "payments", row, "payment currency differs from invoice")
            if _dt(row["payment_datetime"]).date() < date.fromisoformat(invoice["invoice_date"]):
                add("TIME-PAY-001", "payments", row, "payment precedes invoice")
            payments_by_invoice[row["invoice_id"]] = payments_by_invoice.get(
                row["invoice_id"], Decimal("0")
            ) + _dec(row["amount"])
        for row in data["refunds"]:
            payment_amount = next(
                _dec(payment["amount"])
                for payment in data["payments"]
                if payment["payment_id"] == row["payment_id"]
            )
            refunds_by_payment[row["payment_id"]] = refunds_by_payment.get(
                row["payment_id"], Decimal("0")
            ) + _dec(row["refund_amount"])
            refunds_by_invoice[row["invoice_id"]] = refunds_by_invoice.get(
                row["invoice_id"], Decimal("0")
            ) + _dec(row["refund_amount"])
            if refunds_by_payment[row["payment_id"]] > payment_amount:
                add("FIN-REF-001", "refunds", row, "refunds exceed payment")
            payment = next(
                payment
                for payment in data["payments"]
                if payment["payment_id"] == row["payment_id"]
            )
            if _dt(row["refund_datetime"]) < _dt(payment["payment_datetime"]):
                add("TIME-REF-001", "refunds", row, "refund precedes payment")
        for row in data["adjustments"]:
            adjustments_by_invoice[row["invoice_id"]] = adjustments_by_invoice.get(
                row["invoice_id"], Decimal("0")
            ) + _dec(row["adjustment_amount"])
            invoice = invoices[row["invoice_id"]]
            if _dt(row["adjustment_datetime"]).date() < date.fromisoformat(invoice["invoice_date"]):
                add("TIME-ADJ-001", "adjustments", row, "adjustment precedes invoice")
        for row in data["revenue_events"]:
            if _dec(row["amount"]) < 0:
                add("FIN-REV-001", "revenue_events", row, "revenue event amount is negative")
            if row["invoice_id"] and _dt(row["event_datetime"]).date() < date.fromisoformat(
                invoices[row["invoice_id"]]["invoice_date"]
            ):
                add("TIME-REV-001", "revenue_events", row, "revenue event precedes invoice")
        for row in data["outstanding_balances"]:
            expected = (
                _dec(row["invoiced_amount"])
                - _dec(row["payment_amount"])
                + _dec(row["refund_amount"])
                - _dec(row["adjustment_amount"])
            )
            if _dec(row["outstanding_amount"]) != expected:
                add("FIN-BAL-001", "outstanding_balances", row, "outstanding balance mismatch")
            invoice = invoices[row["invoice_id"]]
            if date.fromisoformat(row["snapshot_date"]) < date.fromisoformat(
                invoice["invoice_date"]
            ):
                add("TIME-BAL-001", "outstanding_balances", row, "snapshot precedes invoice")
        amount_fields = {
            "INVOICES": ("invoices", "total_amount", "gross_amount"),
            "INVOICE_LINES": ("invoice_lines", "gross_amount", "gross_amount"),
            "PAYMENTS": ("payments", "amount", "payment_amount"),
            "REFUNDS": ("refunds", "refund_amount", "refund_amount"),
            "ADJUSTMENTS": ("adjustments", "adjustment_amount", "adjustment_amount"),
        }
        for row in data["daily_control_totals"]:
            dataset, amount_field, control_field = amount_fields[row["entity_type"]]
            rows = data[dataset]
            expected_amount = sum((_dec(item[amount_field]) for item in rows), Decimal("0"))
            if row["record_count"] != len(rows) or _dec(row[control_field]) != expected_amount:
                add("FIN-CTL-001", "daily_control_totals", row, "control total mismatch")

    return ValidationReport(
        valid=not issues,
        datasets_validated=len(DATASET_ORDER),
        rows_validated=sum(len(data[name]) for name in DATASET_ORDER),
        issues=tuple(issues),
    )
