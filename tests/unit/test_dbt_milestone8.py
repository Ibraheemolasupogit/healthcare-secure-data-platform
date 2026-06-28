from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[2]
DBT_ROOT = ROOT / "dbt"

BILLING_SOURCES = {
    "payers",
    "services",
    "products",
    "tariffs",
    "contracts",
    "billable_activity",
    "claims",
    "claim_lines",
    "invoices",
    "invoice_lines",
    "payment_attempts",
    "payments",
    "refunds",
    "adjustments",
    "billing_exceptions",
}
FINANCE_SOURCES = {"revenue_events", "outstanding_balances", "daily_control_totals"}


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text())
    assert isinstance(loaded, dict)
    return cast(dict[str, Any], loaded)


def _model_sql(root: Path) -> dict[str, str]:
    return {path.stem: path.read_text().lower() for path in root.glob("**/*.sql")}


def test_billing_and_finance_sources_declared_from_milestone7_contracts() -> None:
    billing = _load_yaml(DBT_ROOT / "models/sources/raw_billing.yml")["sources"][0]
    finance = _load_yaml(DBT_ROOT / "models/sources/raw_finance.yml")["sources"][0]

    assert billing["name"] == "raw_billing"
    assert finance["name"] == "raw_finance"
    assert {table["name"] for table in billing["tables"]} == BILLING_SOURCES
    assert {table["name"] for table in finance["tables"]} == FINANCE_SOURCES

    for source in (billing, finance):
        assert source["meta"]["loader"] == "SYNTHETIC_MILESTONE_7"
        for table in source["tables"]:
            assert table["description"]
            assert table["identifier"] == table["name"].upper()
            assert table["loaded_at_field"]
            assert table["freshness"]["warn_after"]
            assert table["freshness"]["error_after"]
            assert table["meta"]["milestone_owner"] == "milestone_8"
            assert table["meta"]["schema_version"] == "1.0.0"
            assert table["meta"]["synthetic_data"] is True
            assert table["meta"]["sensitivity"] == "synthetic_financial_restricted"
            assert "data_tests" in table


def test_billing_and_finance_staging_inventory_and_boundary() -> None:
    billing_stage = _model_sql(DBT_ROOT / "models/staging/billing")
    finance_stage = _model_sql(DBT_ROOT / "models/staging/finance")

    assert set(billing_stage) == {
        "stg_billing__payers",
        "stg_billing__services",
        "stg_billing__products",
        "stg_billing__tariffs",
        "stg_billing__contracts",
        "stg_billing__billable_activity",
        "stg_billing__claims",
        "stg_billing__claim_lines",
        "stg_billing__invoices",
        "stg_billing__invoice_lines",
        "stg_billing__exceptions",
    }
    assert set(finance_stage) == {
        "stg_finance__payment_attempts",
        "stg_finance__payments",
        "stg_finance__refunds",
        "stg_finance__adjustments",
        "stg_finance__revenue_events",
        "stg_finance__outstanding_balances",
        "stg_finance__daily_control_totals",
    }

    for sql in [*billing_stage.values(), *finance_stage.values()]:
        assert "{{ source(" in sql
        assert "{{ ref(" not in sql
        assert " join " not in sql
        assert "deduplicate_source" in sql
        assert "source_record_id" in sql
        assert "source_relation" in sql
        assert "dbt_loaded_at" in sql
    assert any(
        "financial_decimal" in sql for sql in [*billing_stage.values(), *finance_stage.values()]
    )


def test_curated_billing_finance_inventory_and_core_linkage() -> None:
    billing = _model_sql(DBT_ROOT / "models/curated/billing")
    finance = _model_sql(DBT_ROOT / "models/curated/finance")

    assert set(billing) == {
        "dim_payer",
        "dim_service",
        "dim_product",
        "dim_tariff",
        "dim_contract",
        "fct_billable_activity",
        "fct_claim",
        "fct_claim_line",
        "fct_invoice",
        "fct_invoice_line",
        "billing_exception",
    }
    assert set(finance) == {
        "fct_payment_attempt",
        "fct_payment",
        "bridge_payment_allocation",
        "fct_refund",
        "fct_adjustment",
        "fct_revenue_event",
        "fct_outstanding_balance",
        "finance_daily_control",
    }

    for name, sql in {**billing, **finance}.items():
        assert "{{ source(" not in sql, name
        assert "{{ ref(" in sql, name
        assert "generate_healthcare_surrogate_key" in sql, name
        assert "source_record_id" in sql or name in {"bridge_payment_allocation"}
        assert "dbt_updated_at" in sql

    linked_sql = "\n".join(billing.values())
    for core_model in {
        "core_patient",
        "core_encounter",
        "core_appointment",
        "core_provider",
        "core_organisation",
        "core_clinical_event",
    }:
        assert f"ref('{core_model}')" in linked_sql


def test_single_authoritative_financial_calculation_paths() -> None:
    intermediate_sql = _model_sql(DBT_ROOT / "models/intermediate")
    assert {
        "int_billing__tariff_candidates",
        "int_billing__selected_tariff",
        "int_billing__selected_contract",
        "int_finance__payment_allocations",
        "int_finance__governed_outstanding_balance",
        "int_finance__daily_control_comparison",
    }.issubset(intermediate_sql)

    assert "tariff_match_status" in intermediate_sql["int_billing__selected_tariff"]
    assert "contract_match_status" in intermediate_sql["int_billing__selected_contract"]
    assert (
        "governed_outstanding_amount"
        in intermediate_sql["int_finance__governed_outstanding_balance"]
    )
    assert "allocation_status" in intermediate_sql["int_finance__payment_allocations"]


def test_money_types_currency_and_no_floating_point_finance() -> None:
    all_sql = "\n".join(path.read_text().lower() for path in DBT_ROOT.glob("**/*.sql"))
    assert "float" not in all_sql
    assert "double" not in all_sql
    assert "number(18,2)" in all_sql
    assert "currency_mismatch" in all_sql
    assert "gbp" in (DBT_ROOT / "models/sources/raw_billing.yml").read_text().lower()


def test_contract_metadata_and_model_grains_are_documented() -> None:
    for schema_path in [
        DBT_ROOT / "models/curated/billing/_schema.yml",
        DBT_ROOT / "models/curated/finance/_schema.yml",
    ]:
        for model in _load_yaml(schema_path)["models"]:
            assert model["description"]
            assert model["config"]["contract"]["enforced"] is True
            assert model["meta"]["milestone"] == "8"
            assert model["meta"]["layer"] == "curated_billing_finance"
            assert model["meta"]["contract_status"] == "declared_not_runtime_proven"
            assert model["meta"]["model_grain"]
            assert any(column["name"].endswith("_key") for column in model["columns"])


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
            *DBT_ROOT.glob("models/curated/billing/**/*.sql"),
            *DBT_ROOT.glob("models/curated/finance/**/*.sql"),
            *DBT_ROOT.glob("models/intermediate/billing/**/*.sql"),
            *DBT_ROOT.glob("models/intermediate/finance/**/*.sql"),
        ]
    )
    assert not re.search(
        r"airflow|dataiku|power\\s*bi|feature_store|feature store", changed_scope_text
    )
