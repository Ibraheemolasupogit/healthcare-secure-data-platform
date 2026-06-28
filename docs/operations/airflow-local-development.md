# Airflow local development

Airflow is optional for local development. Normal validation does not install or start Airflow.

Install dependencies explicitly:

```bash
python -m pip install -r requirements-airflow.txt
```

Run static guardrails:

```bash
PYTHONPATH=src pytest tests/unit/test_airflow_milestone10.py
```

Start the opt-in Docker profile:

```bash
docker compose --profile airflow up airflow-init
docker compose --profile airflow up airflow-webserver airflow-scheduler
```

The local profile uses fixture mode, mounts the repository, writes outputs under `outputs/orchestration`, and does not include credentials.
