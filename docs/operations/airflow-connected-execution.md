# Airflow connected execution

Connected Snowflake execution is disabled by default.

To run connected dbt tasks later, an operator must provide authorised credentials through approved Snowflake/dbt mechanisms and set:

```bash
HEALTHCARE_AIRFLOW_EXECUTION_MODE=connected_snowflake
HEALTHCARE_AIRFLOW_CONNECTED_SNOWFLAKE=true
```

Connected mode may run `dbt source freshness`, `dbt build` and `dbt docs generate`. It must not run during normal CI and must not embed secrets in DAGs, Compose files or command strings.

Fixture mode is not live platform execution.
