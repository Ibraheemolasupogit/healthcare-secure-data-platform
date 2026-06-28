"""Generation profile loading, validation and volume estimation."""

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

DEFAULT_PROFILE_PATH = Path("config/synthetic/profiles.json")


@dataclass(frozen=True)
class GenerationProfile:
    """Validated volume and generation controls."""

    name: str
    patient_count: int
    organisation_count: int
    locations_per_organisation: int
    providers_per_organisation: int
    encounters_per_patient: float
    admission_rate: float
    appointments_per_patient: float
    pathways_per_patient: float
    clinical_events_per_patient: float
    pathology_results_per_patient: float
    medication_events_per_patient: float
    consent_rate: float
    cohort_rate: float
    audit_events_per_patient: float
    historical_days: int
    future_horizon_days: int
    chunk_size: int
    defect_injection_rate: float
    payer_count: int
    service_count: int
    product_count: int
    tariff_count: int
    contract_count: int
    billable_activity_rate: float
    claim_generation_rate: float
    invoice_generation_rate: float
    payment_attempt_rate: float
    payment_success_rate: float
    refund_rate: float
    adjustment_rate: float
    claim_rejection_rate: float
    late_payment_rate: float
    billing_exception_rate: float
    balance_snapshot_count: int
    control_total_frequency_days: int
    billing_defect_injection_rate: float
    output_formats: tuple[str, ...]

    def validate(self) -> None:
        """Reject unsafe or nonsensical configuration before writing files."""
        positive = (
            self.patient_count,
            self.organisation_count,
            self.locations_per_organisation,
            self.providers_per_organisation,
            self.historical_days,
            self.chunk_size,
            self.payer_count,
            self.service_count,
            self.product_count,
            self.tariff_count,
            self.contract_count,
            self.balance_snapshot_count,
            self.control_total_frequency_days,
        )
        if any(value <= 0 for value in positive):
            raise ValueError("counts, historical_days and chunk_size must be positive")
        rates = (
            self.admission_rate,
            self.consent_rate,
            self.cohort_rate,
            self.defect_injection_rate,
            self.billable_activity_rate,
            self.claim_generation_rate,
            self.invoice_generation_rate,
            self.payment_attempt_rate,
            self.payment_success_rate,
            self.refund_rate,
            self.adjustment_rate,
            self.claim_rejection_rate,
            self.late_payment_rate,
            self.billing_exception_rate,
            self.billing_defect_injection_rate,
        )
        if any(not 0 <= rate <= 1 for rate in rates):
            raise ValueError("rates must be between 0 and 1")
        if not set(self.output_formats) <= {"csv", "jsonl"} or not self.output_formats:
            raise ValueError("output_formats must contain csv and/or jsonl")

    def with_patient_count(self, count: int | None) -> "GenerationProfile":
        profile = replace(self, patient_count=count) if count is not None else self
        profile.validate()
        return profile

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def estimated_rows(self) -> dict[str, int]:
        n = self.patient_count
        encounters = round(n * self.encounters_per_patient)
        appointments = round(n * self.appointments_per_patient)
        base_activity = round((encounters + appointments) * self.billable_activity_rate)
        claims = round(base_activity * self.claim_generation_rate)
        invoices = round(base_activity * self.invoice_generation_rate)
        attempts = round(invoices * self.payment_attempt_rate)
        payments = round(attempts * self.payment_success_rate)
        return {
            "organisations": self.organisation_count,
            "locations": self.organisation_count * self.locations_per_organisation,
            "providers": self.organisation_count * self.providers_per_organisation,
            "patients": n,
            "encounters": encounters,
            "admissions": round(encounters * self.admission_rate),
            "appointments": appointments,
            "pathways": round(n * self.pathways_per_patient),
            "clinical_events": max(round(n * self.clinical_events_per_patient), appointments),
            "pathology_results": round(n * self.pathology_results_per_patient),
            "medication_events": round(n * self.medication_events_per_patient),
            "research_consent": round(n * self.consent_rate),
            "research_cohorts": round(n * self.consent_rate * self.cohort_rate),
            "audit_events": round(n * self.audit_events_per_patient),
            "data_quality_events": 0,
            "payers": self.payer_count,
            "services": self.service_count,
            "products": self.product_count,
            "tariffs": self.tariff_count,
            "contracts": self.contract_count,
            "billable_activity": base_activity,
            "claims": claims,
            "claim_lines": claims,
            "invoices": invoices,
            "invoice_lines": invoices,
            "payment_attempts": attempts,
            "payments": payments,
            "refunds": round(payments * self.refund_rate),
            "adjustments": round(invoices * self.adjustment_rate),
            "billing_exceptions": round(base_activity * self.billing_exception_rate),
            "revenue_events": invoices + payments,
            "outstanding_balances": invoices * self.balance_snapshot_count,
            "daily_control_totals": 3,
        }


def load_profiles(path: Path = DEFAULT_PROFILE_PATH) -> dict[str, GenerationProfile]:
    raw = json.loads(path.read_text(encoding="utf-8"))["profiles"]
    profiles: dict[str, GenerationProfile] = {}
    for name, values in raw.items():
        values["output_formats"] = tuple(values["output_formats"])
        profile = GenerationProfile(name=name, **values)
        profile.validate()
        profiles[name] = profile
    return profiles


def load_profile(name: str, path: Path = DEFAULT_PROFILE_PATH) -> GenerationProfile:
    profiles = load_profiles(path)
    if name not in profiles:
        raise ValueError(f"unknown profile {name!r}; choose from {', '.join(sorted(profiles))}")
    return profiles[name]
