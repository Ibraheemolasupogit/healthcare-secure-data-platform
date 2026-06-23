"""Research, audit and controlled negative-test generators."""

from datetime import date, timedelta

from healthcare_platform.synthetic import code_sets
from healthcare_platform.synthetic.generators.common import at_utc, iso_date, iso_datetime
from healthcare_platform.synthetic.generators.types import DatasetMap, Record
from healthcare_platform.synthetic.identifiers import stable_id
from healthcare_platform.synthetic.profiles import GenerationProfile
from healthcare_platform.synthetic.random_streams import stream


def generate_governance(
    profile: GenerationProfile,
    seed: int,
    reference_date: date,
    data: DatasetMap,
    inject_defects: bool,
    negative_test_mode: bool,
) -> DatasetMap:
    consent = _consent(profile, seed, reference_date, data["patients"])
    cohorts = _cohorts(profile, reference_date, consent)
    audit = _audit(profile, seed, reference_date)
    quality: list[Record] = []
    if inject_defects:
        if not negative_test_mode:
            raise ValueError("defect injection requires --negative-test-mode and separate output")
        quality = _inject_defects(reference_date, data)
    return {
        "research_consent": consent,
        "research_cohorts": cohorts,
        "audit_events": audit,
        "data_quality_events": quality,
    }


def _consent(
    profile: GenerationProfile, seed: int, reference_date: date, patients: list[Record]
) -> list[Record]:
    rng = stream(seed, "consent")
    count = profile.estimated_rows()["research_consent"]
    rows: list[Record] = []
    for ordinal, patient in enumerate(patients[:count], 1):
        status = code_sets.CONSENT_STATUSES[(ordinal - 1) % len(code_sets.CONSENT_STATUSES)]
        valid_from = reference_date - timedelta(days=rng.randint(180, 900))
        valid_to = None
        withdrawal = None
        if status == "WITHDRAWN":
            withdrawal = valid_from + timedelta(
                days=rng.randint(1, (reference_date - valid_from).days)
            )
        elif status == "EXPIRED":
            valid_to = reference_date - timedelta(days=rng.randint(1, 90))
        elif status == "DECLINED":
            valid_to = valid_from
        allowed = status == "ACTIVE"
        rows.append(
            {
                "consent_id": stable_id("research_consent", ordinal),
                "patient_id": patient["patient_id"],
                "consent_type": "GENERAL_RESEARCH",
                "consent_status": status,
                "valid_from": iso_date(valid_from),
                "valid_to": iso_date(valid_to) if valid_to else None,
                "withdrawal_date": iso_date(withdrawal) if withdrawal else None,
                "research_use_allowed": allowed,
                "updated_at": iso_datetime(at_utc(withdrawal or valid_to or reference_date)),
            }
        )
    return rows


def _cohorts(
    profile: GenerationProfile, reference_date: date, consent: list[Record]
) -> list[Record]:
    eligible = [row for row in consent if row["research_use_allowed"]]
    count = min(profile.estimated_rows()["research_cohorts"], len(eligible))
    rows: list[Record] = []
    for ordinal, consent_row in enumerate(eligible[:count], 1):
        excluded = ordinal % 5 == 0
        rows.append(
            {
                "cohort_membership_id": stable_id("research_cohorts", ordinal),
                "cohort_id": "SYN-COHORT-01",
                "patient_id": consent_row["patient_id"],
                "cohort_name": "Synthetic Outcomes Research Cohort",
                "inclusion_date": iso_date(reference_date - timedelta(days=60)),
                "exclusion_date": iso_date(reference_date - timedelta(days=10))
                if excluded
                else None,
                "inclusion_reason": "VALID_ACTIVE_CONSENT",
                "eligible_flag": True,
                "consent_status_at_inclusion": "ACTIVE",
            }
        )
    return rows


def _audit(profile: GenerationProfile, seed: int, reference_date: date) -> list[Record]:
    rng = stream(seed, "audit")
    rows: list[Record] = []
    for ordinal in range(1, profile.estimated_rows()["audit_events"] + 1):
        rows.append(
            {
                "audit_event_id": stable_id("audit_events", ordinal),
                "actor_id": f"SVC-SYNTHETIC-{(ordinal % 5) + 1:02d}",
                "actor_role": rng.choice(
                    ("DATA_ENGINEER", "QUALITY_ANALYST", "APPROVED_RESEARCHER")
                ),
                "action": rng.choice(code_sets.AUDIT_ACTIONS),
                "object_type": "DATASET",
                "object_id": rng.choice(("patients", "encounters", "pathology_results")),
                "event_datetime": iso_datetime(
                    at_utc(reference_date - timedelta(days=rng.randint(0, 90)))
                ),
                "outcome": rng.choice(("SUCCESS", "DENIED")),
                "source_component": "SYNTHETIC_GENERATOR",
                "environment": "local",
                "correlation_id": f"COR-{ordinal:09d}",
            }
        )
    return rows


def _inject_defects(reference_date: date, data: DatasetMap) -> list[Record]:
    if not data["appointments"]:
        return []
    appointment = data["appointments"][0]
    appointment["attendance_status"] = "CANCELLED"
    appointment["cancellation_reason"] = None
    return [
        {
            "quality_event_id": stable_id("data_quality_events", 1),
            "dataset_name": "appointments",
            "rule_id": "BR-APT-001",
            "rule_name": "Cancelled appointment reason required",
            "severity": "ERROR",
            "record_identifier": appointment["appointment_id"],
            "detected_at": iso_datetime(at_utc(reference_date)),
            "status": "OPEN",
            "resolution_action": "NEGATIVE_TEST_ONLY",
        }
    ]
