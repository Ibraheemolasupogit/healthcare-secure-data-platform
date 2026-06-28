# Airflow configuration

Milestone 10 uses one authoritative configuration layer in `orchestration/airflow/include/configuration.py`.

Important defaults:

- `HEALTHCARE_AIRFLOW_EXECUTION_MODE=fixture`
- `HEALTHCARE_AIRFLOW_CONNECTED_SNOWFLAKE=false`
- `HEALTHCARE_AIRFLOW_ALLOW_LARGE_GENERATION=false`
- `HEALTHCARE_AIRFLOW_OVERWRITE=false`
- `HEALTHCARE_AIRFLOW_CATCHUP=false`
- `HEALTHCARE_AIRFLOW_MAX_ACTIVE_RUNS=1`
- `HEALTHCARE_AIRFLOW_ENABLE_NOTIFICATIONS=false`

Use `.env.example` as the placeholder reference. Do not store secrets in `.env`, Airflow Variables, DAG files or command strings.
