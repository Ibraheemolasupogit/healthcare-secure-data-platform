from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from healthcare_platform.assurance import write_evidence_pack

ROOT = Path(__file__).resolve().parents[2]
DBT_ROOT = ROOT / "dbt"


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text())
    assert isinstance(loaded, dict)
    return cast(dict[str, Any], loaded)


def _model_sql(root: Path) -> dict[str, str]:
    return {path.stem: path.read_text().lower() for path in root.glob("**/*.sql")}


def test_assurance_rule_seeds_are_declared_and_complete() -> None:
    seed_root = DBT_ROOT / "seeds" / "assurance"
    seed_names = {path.stem for path in seed_root.glob("*.csv")}

    assert seed_names == {
        "assurance_exception_ownership",
        "assurance_lifecycle_transitions",
        "assurance_priority_weights",
        "assurance_severity_rules",
        "assurance_tolerance_rules",
    }

    seed_schema = _load_yaml(seed_root / "_schema.yml")
    declared = {seed["name"] for seed in seed_schema["seeds"]}
    assert declared == seed_names
    for seed in seed_schema["seeds"]:
        assert seed["description"]
        assert seed["meta"]["milestone"] == "9"
        assert seed["meta"]["owner"] == "analytics engineering"

    for path in seed_root.glob("*.csv"):
        with path.open(encoding="utf-8", newline="") as handle:
            assert list(csv.DictReader(handle)), path


def test_assurance_models_reference_milestone8_outputs_not_raw_sources() -> None:
    assurance_sql = _model_sql(DBT_ROOT / "models" / "intermediate" / "assurance") | _model_sql(
        DBT_ROOT / "models" / "curated" / "assurance"
    )

    assert {
        "int_assurance__control_results",
        "int_assurance__reconciliation_exceptions",
        "int_assurance__exception_enriched",
        "int_assurance__exception_priority",
        "int_assurance__remediation_state",
        "reconciliation_control_result",
        "reconciliation_exception",
        "exception_lifecycle_event",
        "exception_remediation_status",
        "open_exception_inventory",
        "high_priority_exception_inventory",
        "revenue_at_risk_summary",
        "daily_assurance_summary",
        "month_end_assurance",
        "assurance_evidence_pack",
    }.issubset(assurance_sql)

    combined = "\n".join(assurance_sql.values())
    assert "{{ source(" not in combined
    assert "ref('finance_daily_control')" in combined
    assert "ref('billing_exception')" in combined
    assert "ref('fct_invoice')" in combined
    assert "ref('fct_payment')" in combined
    assert "ref('fct_revenue_event')" in combined
    assert "ref('fct_outstanding_balance')" in combined


def test_assurance_does_not_duplicate_milestone8_financial_calculations() -> None:
    combined = "\n".join(
        path.read_text().lower()
        for path in [
            *DBT_ROOT.glob("models/intermediate/assurance/**/*.sql"),
            *DBT_ROOT.glob("models/curated/assurance/**/*.sql"),
        ]
    )

    prohibited_m8_calculation_refs = {
        "ref('int_billing__tariff_candidates')",
        "ref('int_billing__selected_tariff')",
        "ref('int_billing__selected_contract')",
        "ref('int_billing__claim_line_calculations')",
        "ref('int_billing__invoice_line_calculations')",
        "ref('int_finance__payment_allocations')",
        "ref('int_finance__revenue_event_classification')",
        "ref('int_finance__governed_outstanding_balance')",
    }
    for ref_name in prohibited_m8_calculation_refs:
        assert ref_name not in combined

    assert "financial_value_at_risk" in combined
    assert "include_in_value_at_risk" in combined
    assert "linked_exception_group_key" in combined


def test_exception_lifecycle_priority_and_revenue_risk_contracts_are_documented() -> None:
    schema = _load_yaml(DBT_ROOT / "models" / "curated" / "assurance" / "_schema.yml")
    model_names = {model["name"] for model in schema["models"]}

    assert {
        "reconciliation_control_result",
        "reconciliation_exception",
        "exception_lifecycle_event",
        "exception_remediation_status",
        "open_exception_inventory",
        "high_priority_exception_inventory",
        "revenue_at_risk_summary",
        "daily_assurance_summary",
        "month_end_assurance",
        "assurance_evidence_pack",
    }.issubset(model_names)

    for model in schema["models"]:
        assert model["description"]
        assert model["config"]["contract"]["enforced"] is True
        assert model["meta"]["milestone"] == "9"
        assert model["meta"]["layer"] == "curated_assurance"
        assert model["meta"]["contract_status"] == "declared_not_runtime_proven"
        assert model["meta"]["model_grain"]


def test_assurance_macros_and_project_configuration_are_registered() -> None:
    project = _load_yaml(DBT_ROOT / "dbt_project.yml")
    assert (
        project["models"]["healthcare_secure_data_platform"]["curated"]["assurance"]["+schema"]
        == "assurance"
    )
    assert project["models"]["healthcare_secure_data_platform"]["curated"]["assurance"][
        "+tags"
    ] == ["milestone_9", "assurance"]
    assert project["vars"]["assurance_as_of_date"] == "2025-01-01"
    assert project["seeds"]["healthcare_secure_data_platform"]["assurance"]["+schema"] == (
        "assurance_config"
    )
    assert project["seeds"]["healthcare_secure_data_platform"]["assurance"]["+tags"] == (
        ["milestone_9", "assurance_config"]
    )

    macro_sql = (DBT_ROOT / "macros" / "assurance" / "assurance_rules.sql").read_text().lower()
    for macro_name in {
        "assurance_status",
        "exception_age_days",
        "priority_band",
        "assurance_status_precedence",
    }:
        assert f"macro {macro_name}" in macro_sql


def test_scope_does_not_start_later_milestones() -> None:
    prohibited_paths = [
        "orchestration",
        "dataiku",
        "fabric",
        "dbt/models/marts",
        "dbt/models/semantic",
    ]
    for relative in prohibited_paths:
        sql_files = list((ROOT / relative).glob("**/*.sql")) if (ROOT / relative).exists() else []
        assert not sql_files, relative

    changed_scope_text = "\n".join(
        path.read_text(errors="ignore").lower()
        for path in [
            *DBT_ROOT.glob("models/intermediate/assurance/**/*.sql"),
            *DBT_ROOT.glob("models/curated/assurance/**/*.sql"),
            *DBT_ROOT.glob("macros/assurance/**/*.sql"),
        ]
    )
    for prohibited in ("airflow", "dataiku", "power bi", "feature_store", "feature store"):
        assert prohibited not in changed_scope_text


def test_assurance_evidence_pack_is_deterministic_and_credential_free(tmp_path: Path) -> None:
    first = write_evidence_pack(tmp_path / "first", project_root=ROOT)
    second = write_evidence_pack(tmp_path / "second", project_root=ROOT)

    first_manifest = json.loads(first.manifest_path.read_text())
    second_manifest = json.loads(second.manifest_path.read_text())
    first_manifest.pop("generated_at")
    second_manifest.pop("generated_at")

    assert first_manifest == second_manifest
    assert first_manifest["milestone"] == "9"
    assert first_manifest["file_count"] >= 20
    assert first_manifest["source_boundary"] == (
        "curated_assurance_models_reference_milestone_8_outputs"
    )
    assert first.checksum_path.read_text()
