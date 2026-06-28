"""Bounded local availability checks for Airflow tasks."""

from __future__ import annotations

import hashlib
from pathlib import Path


def require_path(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return str(path)


def require_fixture_dataset(path: Path) -> str:
    for relative in ("manifest.json", "checksums.sha256", "relational/patients.csv"):
        require_path(path / relative)
    return str(path)


def require_interoperability_fixture(path: Path) -> str:
    for relative in (
        "fhir/validation/fhir_validation_report.json",
        "hl7/validation/hl7_validation_report.json",
        "manifests/ingestion_manifest.json",
        "crosswalks/identifier_crosswalk.json",
        "quarantine/quarantine_records.json",
    ):
        require_path(path / relative)
    return str(path)


def verify_checksum_manifest(directory: Path) -> str:
    checksum_path = directory / "checksums.sha256"
    require_path(checksum_path)
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split(maxsplit=1)
        candidate = directory / relative.strip()
        require_path(candidate)
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError(f"checksum mismatch for {candidate}")
    return str(checksum_path)


def verify_no_connected_execution(enabled: bool) -> str:
    if enabled:
        return "connected Snowflake execution explicitly enabled"
    return "connected Snowflake execution disabled"
