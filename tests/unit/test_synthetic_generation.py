from datetime import date

from healthcare_platform.synthetic.generators import generate_all
from healthcare_platform.synthetic.generators.types import DatasetMap
from healthcare_platform.synthetic.profiles import load_profile
from healthcare_platform.synthetic.validation import validate


def _small_data(seed: int = 42) -> DatasetMap:
    profile = load_profile("small").with_patient_count(12)
    return generate_all(profile, seed, date(2025, 1, 1))


def test_generation_is_deterministic_and_seed_sensitive() -> None:
    first = _small_data()
    second = _small_data()
    different = _small_data(43)
    assert first == second
    assert first["patients"] != different["patients"]


def test_clean_generation_passes_integrity_validation() -> None:
    report = validate(_small_data(), date(2025, 1, 1))
    assert report.valid, report.issues
    assert report.datasets_validated == 15


def test_temporal_and_business_rules_detect_mutation() -> None:
    data = _small_data()
    data["appointments"][0]["booking_datetime"] = "2026-01-01T00:00:00Z"
    data["pathology_results"][0]["abnormal_flag"] = not data["pathology_results"][0][
        "abnormal_flag"
    ]
    report = validate(data, date(2025, 1, 1))
    assert not report.valid
    assert {issue.rule_id for issue in report.issues} >= {"TIME-APT-001", "BR-LAB-001"}


def test_negative_mode_records_every_injected_defect() -> None:
    profile = load_profile("small").with_patient_count(12)
    data = generate_all(profile, 42, date(2025, 1, 1), True, True)
    assert len(data["data_quality_events"]) == 1
    report = validate(data, date(2025, 1, 1))
    assert not report.valid
    assert any(
        issue.rule_id == data["data_quality_events"][0]["rule_id"] for issue in report.issues
    )
