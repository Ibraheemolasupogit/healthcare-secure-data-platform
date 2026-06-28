# Milestone 10 evidence

Milestone 10 adds an Apache Airflow orchestration foundation.

## Implemented inventory

- 5 DAG files.
- 5 DAG IDs:
  - `healthcare_source_preparation`
  - `interoperability_ingestion`
  - `healthcare_dbt_pipeline`
  - `billing_assurance_pipeline`
  - `healthcare_platform_end_to_end`
- Shared helper modules for configuration, commands, validation, callbacks and evidence.
- Optional Airflow dependency file pinned to Apache Airflow 2.9.3.
- Opt-in Docker Compose Airflow profile.
- Static guardrail tests in `tests/unit/test_airflow_milestone10.py`.

## Execution status

Fixture mode is the default and does not require Snowflake credentials. Connected Snowflake mode is disabled by default and was not run.

## Validation to perform

```bash
PYTHONPATH=src pytest tests/unit/test_airflow_milestone10.py
make validate
docker compose config
```

If Airflow is installed:

```bash
python -m pip install -r requirements-airflow.txt
airflow dags list
```

## Limitations

- No scheduler-produced run evidence is claimed unless Airflow is actually started.
- No live Snowflake execution is claimed.
- No Dataiku, feature store, Fabric, Power BI, notification or managed Airflow deployment is implemented.

## Milestone 11 hand-off

Milestone 11 may add governed Dataiku workflows that consume trusted products. It must not move dbt or Airflow ownership into Dataiku.
