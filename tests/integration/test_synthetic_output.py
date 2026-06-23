import json
from datetime import date
from pathlib import Path

import pytest

from healthcare_platform.synthetic.manifest import verify_checksums
from healthcare_platform.synthetic.profiles import load_profile
from healthcare_platform.synthetic.service import generate_to_directory, validate_directory


def test_output_manifest_checksums_and_validation(tmp_path: Path) -> None:
    profile = load_profile("small").with_patient_count(10)
    output = tmp_path / "small"
    result = generate_to_directory(profile, 42, date(2025, 1, 1), output)
    assert result.validation.valid
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == 42
    assert manifest["reference_date"] == "2025-01-01"
    assert len(manifest["datasets"]) == 15
    assert verify_checksums(output) == (True, [])
    assert validate_directory(output).valid
    assert "not formally conformant" in (
        output / "fhir_inspired" / "synthetic_bundle.json"
    ).read_text(encoding="utf-8")


def test_equivalent_runs_have_identical_canonical_checksums(tmp_path: Path) -> None:
    profile = load_profile("small").with_patient_count(10)
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_to_directory(profile, 42, date(2025, 1, 1), first)
    generate_to_directory(profile, 42, date(2025, 1, 1), second)
    assert (first / "checksums.sha256").read_bytes() == (second / "checksums.sha256").read_bytes()


def test_overwrite_protection_and_checksum_failure(tmp_path: Path) -> None:
    profile = load_profile("small").with_patient_count(10)
    output = tmp_path / "small"
    generate_to_directory(profile, 42, date(2025, 1, 1), output)
    with pytest.raises(ValueError, match="--overwrite"):
        generate_to_directory(profile, 42, date(2025, 1, 1), output)
    patient_path = output / "relational" / "patients.csv"
    patient_path.write_text(
        patient_path.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8"
    )
    assert not validate_directory(output).valid


def test_negative_outputs_must_be_separated(tmp_path: Path) -> None:
    profile = load_profile("small").with_patient_count(10)
    with pytest.raises(ValueError, match="negative_tests"):
        generate_to_directory(
            profile,
            42,
            date(2025, 1, 1),
            tmp_path / "unsafe",
            inject_defects=True,
            negative_test_mode=True,
        )
    output = tmp_path / "negative_tests" / "small"
    result = generate_to_directory(
        profile, 42, date(2025, 1, 1), output, inject_defects=True, negative_test_mode=True
    )
    assert not result.validation.valid
    assert result.row_counts["data_quality_events"] == 1
