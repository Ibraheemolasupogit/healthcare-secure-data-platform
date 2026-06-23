from pathlib import Path

import pytest

from healthcare_platform.synthetic.profiles import load_profile


def test_profiles_have_expected_scale() -> None:
    assert load_profile("small").patient_count == 100
    assert load_profile("medium").patient_count == 10_000
    assert load_profile("large").patient_count == 1_000_000
    assert load_profile("small").estimated_rows()["clinical_events"] >= 250


def test_invalid_profile_name() -> None:
    with pytest.raises(ValueError, match="unknown profile"):
        load_profile("missing", Path("config/synthetic/profiles.json"))


def test_patient_override_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        load_profile("small").with_patient_count(0)
