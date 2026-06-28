from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[2]
DBT_ROOT = ROOT / "dbt"

FORBIDDEN_MODEL_PATTERNS = (
    re.compile(r"(^|/)dim_", re.IGNORECASE),
    re.compile(r"(^|/)fct_", re.IGNORECASE),
    re.compile(r"(^|/)mart_", re.IGNORECASE),
    re.compile(r"conformed", re.IGNORECASE),
    re.compile(r"billing|tariff|revenue", re.IGNORECASE),
)


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text())
    assert isinstance(loaded, dict)
    return cast(dict[str, Any], loaded)


def _source_tables() -> list[tuple[str, dict[str, Any]]]:
    tables: list[tuple[str, dict[str, Any]]] = []
    milestone5_sources = {
        "raw_clinical",
        "raw_operational",
        "raw_audit",
        "raw_quarantine",
        "raw_interoperability",
        "governance_control",
        "governance_data_quality",
    }
    for path in sorted((DBT_ROOT / "models" / "sources").glob("*.yml")):
        document = _load_yaml(path)
        for source in document["sources"]:
            source_name = source["name"]
            if source_name not in milestone5_sources:
                continue
            for table in source["tables"]:
                tables.append((source_name, table))
    return tables


def test_single_dbt_project_remains_authoritative() -> None:
    projects = sorted(
        path
        for path in ROOT.glob("**/dbt_project.yml")
        if ".venv" not in path.parts and "dbt_packages" not in path.parts
    )
    assert projects == [DBT_ROOT / "dbt_project.yml"]


def test_declared_sources_match_milestone_2_and_4_contracts() -> None:
    schema_catalog = json.loads((ROOT / "data/samples/small/schema_catalog.json").read_text())
    interoperability_contracts = json.loads(
        (ROOT / "snowflake/contracts/interoperability_raw_contracts.json").read_text()
    )
    billing_contracts = json.loads(
        (ROOT / "snowflake/contracts/billing_finance_raw_contracts.json").read_text()
    )
    billing_source_datasets = {
        dataset for datasets in billing_contracts["schemas"].values() for dataset in datasets
    }
    expected = set(schema_catalog)
    expected.difference_update(billing_source_datasets)
    expected.update(
        contract["name"].lower() for contract in interoperability_contracts["contracts"]
    )

    declared = {table["name"] for _, table in _source_tables()}

    assert declared == expected
    assert not declared.intersection(billing_source_datasets)
    assert len(declared) == 23


def test_sources_have_freshness_ownership_and_contract_metadata() -> None:
    for source_name, table in _source_tables():
        assert source_name in {
            "raw_clinical",
            "raw_operational",
            "raw_audit",
            "raw_quarantine",
            "raw_interoperability",
            "governance_control",
            "governance_data_quality",
        }
        assert table["description"]
        assert table["loaded_at_field"]
        assert table["freshness"]["warn_after"]
        assert table["freshness"]["error_after"]
        meta = table["meta"]
        assert meta["owner"]
        assert meta["sensitivity"] == "synthetic_restricted"
        assert meta["schema_version"] == "1.0.0"
        assert meta["milestone_owner"] == "milestone_5"
        assert meta["implementation_status"] in {
            "local_fixture_planned_raw",
            "local_fixture_static_contract",
            "static_contract_not_deployed",
        }
        assert "data_tests" in table


def test_staging_models_are_source_aligned_and_do_not_start_later_layers() -> None:
    model_paths = sorted(
        path
        for path in (DBT_ROOT / "models" / "staging").glob("*/*.sql")
        if path.parent.name not in {"billing", "finance"}
    )
    assert len(model_paths) == 23

    for path in model_paths:
        name = path.stem
        sql = path.read_text().lower()
        assert name.startswith("stg_")
        assert "{{ source(" in sql
        assert "{{ ref(" not in sql
        assert " join " not in sql
        assert "deduplicate_source" in sql
        assert "source_record_id" in sql
        assert "source_relation" in sql
        assert "dbt_loaded_at" in sql
        assert "dbt_invocation_id" in sql
        assert not any(pattern.search(path.as_posix()) for pattern in FORBIDDEN_MODEL_PATTERNS)
        assert not any(pattern.search(sql) for pattern in FORBIDDEN_MODEL_PATTERNS)


def test_interoperability_staging_preserves_source_format_boundary() -> None:
    fhir_sql = (
        DBT_ROOT / "models/staging/interoperability/stg_interoperability__fhir_resources.sql"
    ).read_text()
    hl7_sql = (
        DBT_ROOT / "models/staging/interoperability/stg_interoperability__hl7_messages.sql"
    ).read_text()

    assert "source('raw_interoperability', 'fhir_raw_payloads')" in fhir_sql
    assert "resource_type" in fhir_sql
    assert "resource_id" in fhir_sql
    assert "payload" in fhir_sql
    assert "source('raw_interoperability', 'hl7_raw_messages')" in hl7_sql
    assert "message_control_id" in hl7_sql
    assert "raw_message" in hl7_sql
    assert "dim_patient" not in fhir_sql.lower() + hl7_sql.lower()
    assert "fct_encounter" not in fhir_sql.lower() + hl7_sql.lower()


def test_dbt_macros_are_staging_utilities_only() -> None:
    macro_names = {path.stem for path in (DBT_ROOT / "macros/staging").glob("*.sql")}
    assert macro_names == {
        "deduplicate_source",
        "normalise_code",
        "normalise_empty_string",
        "safe_casts",
    }

    combined = "\n".join(
        path.read_text().lower() for path in (DBT_ROOT / "macros").glob("**/*.sql")
    )
    assert "tariff" not in combined
    assert "revenue" not in combined
    assert "risk_score" not in combined


def test_staging_documentation_has_contract_and_downstream_boundary_metadata() -> None:
    for schema_path in sorted((DBT_ROOT / "models/staging").glob("*/_schema.yml")):
        if schema_path.parent.name in {"billing", "finance"}:
            continue
        document = _load_yaml(schema_path)
        for model in document["models"]:
            assert model["description"]
            assert model["config"]["contract"]["enforced"] is False
            meta = model["meta"]
            assert meta["milestone"] == "5"
            assert meta["layer"] == "staging"
            assert meta["contains_conformed_entity"] is False
            assert meta["downstream_milestone"] == "milestone_6_core_models"
