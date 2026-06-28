# Orchestration evidence

Milestone 10 evidence is local and deterministic.

Evidence artifacts may include:

- `workflow_run_manifest.json`;
- `task_execution_summary.csv`;
- `failure_events.jsonl`;
- `checksums.sha256`;
- `orchestration_summary.md`.

The helper module `orchestration/airflow/include/evidence.py` writes these records without requiring an Airflow scheduler. Label fixture-mode evidence as locally simulated, DAG-structure validated, not Snowflake-connected and not production.
