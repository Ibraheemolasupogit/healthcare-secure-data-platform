# Airflow orchestration architecture

Milestone 10 introduces Apache Airflow as the cross-platform orchestration layer.

Airflow owns schedules, dependencies, retries, timeouts, sensors, callbacks, backfill parameters and workflow-run metadata. It does not own synthetic-data generation, interoperability parsing, Snowflake infrastructure, dbt SQL transformations, billing calculations or assurance calculations.

The DAGs invoke existing repository contracts:

- `healthcare-platform generate` and validation commands;
- `healthcare-platform interoperability ...`;
- `healthcare-platform snowflake-validate` and `snowflake-render`;
- `dbt parse`, `dbt source freshness`, `dbt build` and `dbt docs generate`;
- `healthcare-platform assurance-evidence`.

Execution modes:

- `fixture` — default, credential-free, uses committed samples and static validation.
- `local_generation` — creates isolated deterministic local outputs.
- `connected_snowflake` — optional and disabled by default; requires authorised external credentials.

No managed Airflow service, Kubernetes deployment, production notification integration or live Snowflake execution is claimed.

Future Dataiku integration contract: Airflow validates trusted inputs, invokes one approved Dataiku scenario, receives scenario status and artefact references, and records cross-platform evidence. Milestone 11 does not add live Dataiku API calls to Airflow.
