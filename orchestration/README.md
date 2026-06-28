# Orchestration

Milestone 10 implements a local-first Apache Airflow orchestration foundation.

Airflow coordinates cross-platform dependencies only. It invokes existing Python CLI and dbt contracts rather than recreating their internal logic. It owns schedules, dependencies, retries, timeouts, sensors, callbacks, backfill parameters and workflow metadata.

Normal repository validation remains credential-free and does not start a scheduler. The local Airflow stack is opt-in through the Docker Compose `airflow` profile.
