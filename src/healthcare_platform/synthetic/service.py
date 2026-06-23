"""High-level generation and validation workflows."""

import shutil
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from healthcare_platform.synthetic.generators import generate_all
from healthcare_platform.synthetic.manifest import verify_checksums, write_checksums, write_manifest
from healthcare_platform.synthetic.profiles import GenerationProfile
from healthcare_platform.synthetic.validation import load_csv_datasets, validate
from healthcare_platform.synthetic.validation.report import ValidationReport
from healthcare_platform.synthetic.writers import write_canonical, write_fhir_inspired


@dataclass(frozen=True)
class GenerationResult:
    output_dir: Path
    row_counts: dict[str, int]
    validation: ValidationReport


def generate_to_directory(
    profile: GenerationProfile,
    seed: int,
    reference_date: date,
    output_dir: Path,
    overwrite: bool = False,
    inject_defects: bool = False,
    negative_test_mode: bool = False,
) -> GenerationResult:
    if output_dir.exists() and any(output_dir.iterdir()):
        if not overwrite:
            raise ValueError(
                f"output directory is not empty: {output_dir}; pass --overwrite to replace it"
            )
        shutil.rmtree(output_dir)
    if negative_test_mode and "negative_tests" not in output_dir.parts:
        raise ValueError("negative-test output must be placed under a negative_tests directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    data = generate_all(profile, seed, reference_date, inject_defects, negative_test_mode)
    report = validate(data, reference_date)
    files = write_canonical(data, output_dir, profile.output_formats, profile.chunk_size)
    files.append(write_fhir_inspired(data, output_dir))
    files.extend(report.write(output_dir))
    _, checksums = write_checksums(output_dir, files)
    write_manifest(
        output_dir,
        data,
        profile,
        seed,
        reference_date.isoformat(),
        checksums,
        inject_defects,
        time.perf_counter() - started,
        report.valid,
    )
    return GenerationResult(output_dir, {name: len(rows) for name, rows in data.items()}, report)


def validate_directory(input_dir: Path) -> ValidationReport:
    manifest_path = input_dir / "manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"manifest is missing: {manifest_path}")
    import json

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    reference_date = date.fromisoformat(manifest["reference_date"])
    data = load_csv_datasets(input_dir)
    report = validate(data, reference_date)
    checksum_valid, failures = verify_checksums(input_dir)
    if not checksum_valid:
        from healthcare_platform.synthetic.validation.report import ValidationIssue

        report = ValidationReport(
            False,
            report.datasets_validated,
            report.rows_validated,
            report.issues
            + tuple(
                ValidationIssue("CHECKSUM-001", "output", failure, "checksum mismatch")
                for failure in failures
            ),
        )
    return report
