# Docker development image

The single `dev` service pins Python and installs dbt Core plus credential-free validation tools. It is intentionally not a Snowflake emulator.

Milestone 10 adds an optional Airflow profile for local DAG exploration without burdening the default loop:

```bash
docker compose --profile airflow up airflow-init
docker compose --profile airflow up airflow-webserver airflow-scheduler
```

The Airflow profile is fixture-mode by default and does not include credentials.
