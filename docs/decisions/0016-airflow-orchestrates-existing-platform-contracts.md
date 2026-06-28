# ADR 0016: Airflow orchestrates existing platform contracts

## Status

Accepted.

## Date

2026-06-28

## Context

The platform now has local synthetic generation, interoperability processing, Snowflake foundation previews, dbt transformations and assurance evidence. Milestone 10 needs orchestration without duplicating any of those responsibilities.

## Decision

Apache Airflow owns cross-platform workflow coordination: schedules, dependencies, retries, timeouts, sensors, callbacks, backfill parameters and workflow metadata.

Airflow tasks invoke existing CLI and dbt commands. They do not embed SQL business transformations, recreate parsers, provision Snowflake objects, assign exceptions outside dbt assurance logic or call external notification systems.

Airflow dependencies are optional and separated in `requirements-airflow.txt`. The Docker Compose Airflow stack is opt-in via the `airflow` profile. Fixture mode remains the default; connected Snowflake mode requires explicit enablement.

## Consequences

- Normal CI remains credential-free and lightweight.
- DAG structure can be statically tested without a scheduler.
- Connected execution can be added later without changing ownership boundaries.

## Alternatives considered

- Add Airflow to the default Python dependency set. Rejected because it would make ordinary development heavier.
- Implement transformations directly in Python operators. Rejected because dbt owns transformation logic.
- Use managed Airflow or Kubernetes. Rejected as outside Milestone 10.

## Validation

- `PYTHONPATH=src pytest tests/unit/test_airflow_milestone10.py`.
- `docker compose config`.
- Existing `make validate` gates.
