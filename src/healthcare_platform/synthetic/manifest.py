"""Manifest, provenance and checksum support."""

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from healthcare_platform import __version__
from healthcare_platform.synthetic.generators.types import DatasetMap
from healthcare_platform.synthetic.profiles import GenerationProfile
from healthcare_platform.synthetic.schemas import DATASET_ORDER, SCHEMAS


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def configuration_hash(profile: GenerationProfile, seed: int, reference_date: str) -> str:
    payload = {"profile": profile.as_dict(), "seed": seed, "reference_date": reference_date}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def source_identifier() -> str:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        ).stdout.strip()
        return f"{commit}-dirty" if dirty else commit
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def write_checksums(output_dir: Path, files: list[Path]) -> tuple[Path, dict[str, str]]:
    checksums = {
        path.relative_to(output_dir).as_posix(): sha256_file(path)
        for path in sorted(files)
        if path.name not in {"manifest.json", "checksums.sha256", "summary.md"}
    }
    path = output_dir / "checksums.sha256"
    path.write_text(
        "".join(f"{digest}  {relative}\n" for relative, digest in sorted(checksums.items())),
        encoding="utf-8",
    )
    return path, checksums


def verify_checksums(output_dir: Path) -> tuple[bool, list[str]]:
    checksum_path = output_dir / "checksums.sha256"
    failures: list[str] = []
    if not checksum_path.exists():
        return False, ["checksums.sha256 is missing"]
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", maxsplit=1)
        path = output_dir / relative
        if not path.exists() or sha256_file(path) != expected:
            failures.append(relative)
    return not failures, failures


def write_manifest(
    output_dir: Path,
    data: DatasetMap,
    profile: GenerationProfile,
    seed: int,
    reference_date: str,
    checksums: dict[str, str],
    defect_injection: bool,
    runtime_seconds: float,
    validation_passed: bool,
) -> tuple[Path, Path]:
    datasets: list[dict[str, Any]] = []
    for name in DATASET_ORDER:
        files = [
            {"path": path, "format": "csv" if path.endswith(".csv") else "jsonl", "sha256": digest}
            for path, digest in sorted(checksums.items())
            if path in {f"relational/{name}.csv", f"json/{name}.jsonl"}
        ]
        datasets.append(
            {
                "name": name,
                "row_count": len(data[name]),
                "schema_version": SCHEMAS[name].schema_version,
                "files": files,
            }
        )
    manifest = {
        "project_name": "Healthcare Secure Data Platform",
        "synthetic_data_statement": "All records are deterministic synthetic portfolio data.",
        "generator_version": __version__,
        "profile": profile.name,
        "seed": seed,
        "reference_date": reference_date,
        "generation_timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "configuration_hash": configuration_hash(profile, seed, reference_date),
        "source_code_identifier": source_identifier(),
        "datasets": datasets,
        "output_formats": list(profile.output_formats),
        "defect_injection_enabled": defect_injection,
        "validation_passed": validation_passed,
        "warnings": ["FHIR-inspired resources are not formally conformant."],
        "runtime_duration_seconds": round(runtime_seconds, 6),
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary_path = output_dir / "summary.md"
    lines = [
        "# Synthetic generation summary",
        "",
        "All records in this output are synthetic.",
        "",
        f"- Profile: `{profile.name}`",
        f"- Seed: `{seed}`",
        f"- Reference date: `{reference_date}`",
        f"- Validation: **{'PASS' if validation_passed else 'FAIL'}**",
        f"- Defect injection: `{str(defect_injection).lower()}`",
        "",
        "## Row counts",
        "",
        "| Dataset | Rows |",
        "|---|---:|",
    ]
    lines.extend(f"| `{name}` | {len(data[name])} |" for name in DATASET_ORDER)
    lines.append("")
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return manifest_path, summary_path
