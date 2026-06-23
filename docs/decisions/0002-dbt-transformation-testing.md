# ADR 0002: dbt for transformation and testing

- **Status:** Accepted
- **Date:** 2026-06-23

## Context

SQL transformations need modularity, tests, contracts, documentation, lineage, incremental processing and team-aware CI.

## Decision

dbt owns transformations from STAGING through SEMANTIC, plus source definitions/freshness, tests, snapshots, docs, exposures and future Slim CI. Python and BI tools will not duplicate these transformations.

## Consequences

Lineage and review become code-centric. Adapter behaviour and state artifacts require version discipline and Snowflake-backed integration tests.

## Alternatives considered

Stored procedures obscure lineage; Python dataframes add a second transformation runtime; BI-only logic fragments definitions.

## Validation

Parse in Milestone 1; execute source-to-mart builds, tests and artifact checks in Milestones 5–7 and 14.
