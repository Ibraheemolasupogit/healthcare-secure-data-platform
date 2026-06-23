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
        )
        if any(value <= 0 for value in positive):
            raise ValueError("counts, historical_days and chunk_size must be positive")
        rates = (
            self.admission_rate,
            self.consent_rate,
            self.cohort_rate,
            self.defect_injection_rate,
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
