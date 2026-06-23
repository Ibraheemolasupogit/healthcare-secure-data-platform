# Orchestration

Airflow is deferred to Milestone 11 and will coordinate cross-platform dependencies only. It will invoke dbt jobs and observe Snowflake-native work rather than recreate their internal graphs. `airflow/` will gain a minimal DAG, tests and runbook only when a real external dependency exists.
