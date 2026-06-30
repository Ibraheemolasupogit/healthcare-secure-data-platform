# Orchestration

Milestone 14 governance mapping requires Airflow connected mode to remain disabled by
default, service identity to be documented, command strings to avoid secrets, callbacks to
avoid patient payloads and connected executions to produce audit evidence. Airflow remains
the cross-platform orchestrator.

Milestone 15 deployment controls treat DAG promotion as a versioned bundle with checksum,
approval, rollback reference and environment-specific configuration. No scheduler
deployment is performed.

Milestone 16 recovery controls require DAG bundle checksum validation, paused-DAG default
after recovery, metadata database recovery design and controlled catch-up review. No
Airflow failover or scheduler restore is performed.

Milestone 10 implements a local-first Apache Airflow orchestration foundation.

Airflow coordinates cross-platform dependencies only. It invokes existing Python CLI and dbt contracts rather than recreating their internal logic. It owns schedules, dependencies, retries, timeouts, sensors, callbacks, backfill parameters and workflow metadata.

Normal repository validation remains credential-free and does not start a scheduler. The local Airflow stack is opt-in through the Docker Compose `airflow` profile.
## Milestone 17 operations boundary

Operational readiness consumes Airflow DAG import, dependency, connected-mode,
run-manifest and callback metadata as local health checks. It does not start a
scheduler, emit live alerts or automate production remediation.
