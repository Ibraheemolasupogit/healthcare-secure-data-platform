# ADR 0003: Separate Snowflake-native scheduling from Airflow

- **Status:** Accepted
- **Date:** 2026-06-23

## Context

Duplicating schedules and retry semantics across Snowflake, dbt and Airflow creates ambiguous ownership.

## Decision

Use Snowflake Tasks for platform-local change processing and dbt's selected execution mechanism for transformation jobs. Introduce Airflow only for workflows with genuine cross-platform dependencies, while invoking—not recreating—dbt jobs.

## Consequences

Operational ownership is clearer, though monitoring must correlate multiple schedulers. Airflow is intentionally deferred.

## Alternatives considered

Airflow for every task centralises the UI but duplicates native capabilities; Tasks for external work cannot coordinate systems safely.

## Validation

Milestones 8 and 11 must document each workflow owner and prove no duplicate scheduler can trigger the same unit concurrently.
