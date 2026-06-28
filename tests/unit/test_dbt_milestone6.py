from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[2]
DBT_ROOT = ROOT / "dbt"
CORE_ROOT = DBT_ROOT / "models" / "curated" / "core"

PROHIBITED_SQL = re.compile(
    r"\bsource\s*\(|\bdim_|\bfct_|\bmart_|\bbilling\b|\btariff\b|\brevenue\b|"
    r"\binvoice\b|\bpayment\b|\brefund\b|\bairflow\b|\bdataiku\b|\bfabric\b|"
    r"\bpower\s+bi\b|\bfeature\s+store\b",
    re.IGNORECASE,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text())
    assert isinstance(loaded, dict)
    return cast(dict[str, Any], loaded)


def _models_from_schema(path: Path) -> list[dict[str, Any]]:
    document = _load_yaml(path)
    return cast(list[dict[str, Any]], document["models"])


def test_single_dbt_project_still_remains_authoritative() -> None:
    projects = sorted(
        path
        for path in ROOT.glob("**/dbt_project.yml")
        if ".venv" not in path.parts and "dbt_packages" not in path.parts
    )
    assert projects == [DBT_ROOT / "dbt_project.yml"]


def test_core_model_inventory_and_authoritative_concepts() -> None:
    expected = {
        "core_patient_identity",
        "core_patient",
        "core_organisation",
        "core_location",
        "core_provider",
        "core_encounter",
        "core_admission",
        "core_appointment",
        "core_pathway",
        "core_clinical_event",
        "core_pathology_result",
        "core_medication_event",
        "core_consent",
        "core_research_eligibility",
        "core_reconciliation_exceptions",
        "core_reconciliation_row_counts",
    }
    actual = {path.stem for path in CORE_ROOT.glob("**/*.sql")}
    assert actual == expected


def test_core_models_use_refs_and_never_bypass_staging_sources() -> None:
    for path in CORE_ROOT.glob("**/*.sql"):
        sql = path.read_text()
        assert "{{ ref(" in sql
        assert not PROHIBITED_SQL.search(sql), path
        assert "source_record_id" in sql or "reconciliation" in path.stem
        assert "dbt_updated_at" in sql


def test_intermediate_models_are_the_only_identity_reconciliation_layer() -> None:
    identity_models = sorted((DBT_ROOT / "models" / "intermediate" / "identity").glob("*.sql"))
    assert [path.stem for path in identity_models] == [
        "int_identity__encounter_identifiers",
        "int_identity__patient_identifiers",
    ]
    combined = "\n".join(path.read_text().lower() for path in identity_models)
    assert "probabilistic" not in combined
    assert "source('raw" not in combined
    assert "stg_interoperability__identifier_crosswalks" in combined
    assert "stg_interoperability__ingestion_envelopes" in combined


def test_core_contracts_and_documentation_are_present() -> None:
    schema_paths = [
        CORE_ROOT / "entities" / "_schema.yml",
        CORE_ROOT / "reconciliation" / "_schema.yml",
    ]
    model_names: set[str] = set()
    for schema_path in schema_paths:
        for model in _models_from_schema(schema_path):
            model_names.add(model["name"])
            assert model["description"]
            assert model["config"]["contract"]["enforced"] is True
            assert model["meta"]["milestone"] == "6"
            assert model["meta"]["layer"] == "curated_core"
            assert model["meta"]["contract_status"] == "declared_not_runtime_proven"
            assert model["columns"]
            assert any(column["name"].endswith("_key") for column in model["columns"])
    assert "core_patient" in model_names
    assert "core_encounter" in model_names


def test_core_surrogate_key_macro_is_sha256_and_null_safe() -> None:
    macro = (DBT_ROOT / "macros/core/generate_healthcare_surrogate_key.sql").read_text().lower()
    assert "sha2" in macro
    assert "concat_ws" in macro
    assert "coalesce" in macro
    assert "row_number" not in macro
    assert "random" not in macro


def test_milestone6_does_not_mutate_milestone5_staging_contracts() -> None:
    for path in (DBT_ROOT / "models" / "staging").glob("**/*.sql"):
        sql = path.read_text().lower()
        assert "{{ source(" in sql
        assert "{{ ref(" not in sql
        assert "core_" not in sql


def test_manifest_contains_core_models_after_parse() -> None:
    manifest_path = DBT_ROOT / "target" / "manifest.json"
    # dbt can leave multiple JSON documents after interrupted tool calls; use the first document.
    raw = manifest_path.read_text()
    decoder = json.JSONDecoder()
    manifest, _ = decoder.raw_decode(raw)
    nodes = cast(dict[str, dict[str, Any]], manifest["nodes"])
    core_models = {
        node["name"]
        for node in nodes.values()
        if node["resource_type"] == "model" and node["name"].startswith("core_")
    }
    assert "core_patient" in core_models
    assert "core_reconciliation_exceptions" in core_models
