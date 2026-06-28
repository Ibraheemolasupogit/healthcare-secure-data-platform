"""Milestone 10 orchestration constants."""

from __future__ import annotations

AIRFLOW_VERSION = "2.9.3"
SUPPORTED_EXECUTION_MODES = ("fixture", "local_generation", "connected_snowflake")
DEFAULT_START_DATE = "2025-01-01T00:00:00+00:00"
MILESTONE_10_TAGS = ("milestone_10", "airflow", "orchestration", "synthetic")

DBT_SELECTORS = {
    "staging": "path:models/staging",
    "core": "tag:core",
    "billing": "tag:billing",
    "finance": "tag:finance",
    "assurance": "tag:assurance",
}

DATASET_MARKERS = {
    "synthetic_sources_ready": "synthetic_sources_ready",
    "interoperability_batch_validated": "interoperability_batch_validated",
    "dbt_staging_ready": "dbt_staging_ready",
    "healthcare_core_ready": "healthcare_core_ready",
    "billing_finance_ready": "billing_finance_ready",
    "assurance_controls_ready": "assurance_controls_ready",
    "assurance_evidence_ready": "assurance_evidence_ready",
}
