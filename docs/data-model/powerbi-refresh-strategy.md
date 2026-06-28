# Power BI refresh strategy

Refresh is a blueprint, not a live service configuration.

Refresh groups:

- intraday operational;
- daily finance;
- daily assurance;
- periodic reference data;
- model-output refresh.

Incremental refresh is specified for operational, finance, assurance and model-output
facts using deterministic event or snapshot timestamps. Query folding is not claimed
because no live Power BI/Snowflake connection was executed.

Airflow remains the cross-platform orchestrator. A later deployment milestone may allow
Airflow to call approved Power BI or Fabric refresh endpoints after dbt, assurance,
Dataiku and feature-store readiness checks complete.
