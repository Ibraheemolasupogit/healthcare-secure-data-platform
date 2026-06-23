"""Deterministic identifier and crosswalk rules."""

import hashlib
from dataclasses import asdict, dataclass
from typing import Any


def stable_digest(*parts: str, length: int = 24) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:length]


def ingestion_id(batch_id: str, source_format: str, source_record_id: str) -> str:
    return f"ING-{stable_digest(batch_id, source_format, source_record_id)}"


@dataclass(frozen=True)
class CrosswalkEntry:
    source_format: str
    source_system: str
    identifier_type: str
    source_identifier: str
    canonical_identifier: str
    mapping_rule_version: str = "1.0.0"
    mapping_status: str = "MAPPED"
    synthetic_flag: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_crosswalk(entries: list[CrosswalkEntry]) -> list[dict[str, Any]]:
    """Reject ambiguous mappings and return stable de-duplicated rows."""
    mapped: dict[tuple[str, str, str], CrosswalkEntry] = {}
    for entry in entries:
        key = (entry.source_format, entry.identifier_type, entry.source_identifier)
        if key in mapped and mapped[key].canonical_identifier != entry.canonical_identifier:
            raise ValueError(f"conflicting identifier mapping: {key}")
        mapped[key] = entry
    return [mapped[key].as_dict() for key in sorted(mapped)]
