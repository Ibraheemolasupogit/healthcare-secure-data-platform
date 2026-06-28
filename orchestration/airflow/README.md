# Apache Airflow orchestration

Milestone 10 adds five DAGs:

- `healthcare_source_preparation`
- `interoperability_ingestion`
- `healthcare_dbt_pipeline`
- `billing_assurance_pipeline`
- `healthcare_platform_end_to_end`

The DAGs use helper modules under `include/` for typed configuration, safe command construction, bounded validation checks, callbacks and local evidence metadata.

Fixture mode is the default and uses committed synthetic samples without Snowflake credentials. Connected Snowflake mode is disabled unless explicitly configured.

Run static checks:

```bash
PYTHONPATH=src pytest tests/unit/test_airflow_milestone10.py
```

Optional local Airflow:

```bash
python -m pip install -r requirements-airflow.txt
docker compose --profile airflow up airflow-init
docker compose --profile airflow up airflow-webserver airflow-scheduler
```
