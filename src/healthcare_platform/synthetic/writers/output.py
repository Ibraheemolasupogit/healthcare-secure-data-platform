"""Deterministic CSV, JSON Lines, schema and FHIR-inspired writers."""

import csv
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from healthcare_platform.synthetic.generators.types import DatasetMap
from healthcare_platform.synthetic.schemas import DATASET_ORDER, SCHEMAS


def _normalise_csv(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def _chunks(records: list[dict[str, Any]], chunk_size: int) -> Iterator[list[dict[str, Any]]]:
    """Return stable write batches; generation itself remains in-memory in Milestone 2."""
    for start in range(0, len(records), chunk_size):
        yield records[start : start + chunk_size]


def write_canonical(
    data: DatasetMap, output_dir: Path, formats: tuple[str, ...], chunk_size: int
) -> list[Path]:
    """Write canonical records with stable ordering and line endings."""
    written: list[Path] = []
    if "csv" in formats:
        relational = output_dir / "relational"
        relational.mkdir(parents=True, exist_ok=True)
        for dataset in DATASET_ORDER:
            path = relational / f"{dataset}.csv"
            fieldnames = [field.name for field in SCHEMAS[dataset].fields]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
                writer.writeheader()
                for chunk in _chunks(data[dataset], chunk_size):
                    for record in chunk:
                        writer.writerow(
                            {key: _normalise_csv(record.get(key)) for key in fieldnames}
                        )
                    handle.flush()
            written.append(path)
    if "jsonl" in formats:
        json_dir = output_dir / "json"
        json_dir.mkdir(parents=True, exist_ok=True)
        for dataset in DATASET_ORDER:
            path = json_dir / f"{dataset}.jsonl"
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                for chunk in _chunks(data[dataset], chunk_size):
                    for record in chunk:
                        handle.write(
                            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                        )
                    handle.flush()
            written.append(path)
    schema_path = output_dir / "schema_catalog.json"
    schema_path.write_text(
        json.dumps(
            {name: schema.as_dict() for name, schema in SCHEMAS.items()}, indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(schema_path)
    return written


def write_fhir_inspired(data: DatasetMap, output_dir: Path, limit: int = 3) -> Path:
    """Write a small, explicitly non-conformant FHIR-inspired bundle."""
    patient_ids = {row["patient_id"] for row in data["patients"][:limit]}
    resources: list[dict[str, Any]] = []
    for row in data["organisations"][:2]:
        resources.append(
            {
                "resourceType": "Organization",
                "id": row["organisation_id"],
                "name": row["organisation_name"],
                "meta": {"tag": [{"code": "SYNTHETIC-NON-CONFORMANT"}]},
            }
        )
    for row in data["providers"][:2]:
        resources.append(
            {
                "resourceType": "Practitioner",
                "id": row["provider_id"],
                "name": [{"text": row["provider_label"]}],
                "meta": {"tag": [{"code": "SYNTHETIC-NON-CONFORMANT"}]},
            }
        )
    for row in data["patients"][:limit]:
        resources.append(
            {
                "resourceType": "Patient",
                "id": row["patient_id"],
                "birthDate": row["birth_date"],
                "gender": str(row["sex"]).lower(),
                "meta": {"tag": [{"code": "SYNTHETIC-NON-CONFORMANT"}]},
            }
        )
    for row in (item for item in data["encounters"] if item["patient_id"] in patient_ids):
        resources.append(
            {
                "resourceType": "Encounter",
                "id": row["encounter_id"],
                "subject": {"reference": f"Patient/{row['patient_id']}"},
                "status": str(row["status"]).lower(),
                "period": {"start": row["start_datetime"], "end": row["end_datetime"]},
                "meta": {"tag": [{"code": "SYNTHETIC-NON-CONFORMANT"}]},
            }
        )
    for row in (item for item in data["clinical_events"] if item["patient_id"] in patient_ids):
        resources.append(
            {
                "resourceType": "Observation",
                "id": row["clinical_event_id"],
                "subject": {"reference": f"Patient/{row['patient_id']}"},
                "code": {"text": row["event_code"]},
                "effectiveDateTime": row["event_datetime"],
                "meta": {"tag": [{"code": "SYNTHETIC-NON-CONFORMANT"}]},
            }
        )
    fhir_dir = output_dir / "fhir_inspired"
    fhir_dir.mkdir(parents=True, exist_ok=True)
    path = fhir_dir / "synthetic_bundle.json"
    bundle = {
        "disclaimer": (
            "FHIR-inspired synthetic resources; not validated and not formally conformant."
        ),
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": resource} for resource in resources],
    }
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
