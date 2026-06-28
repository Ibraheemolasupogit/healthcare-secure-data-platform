# ADR 0018: Offline-first governed feature store

## Status

Accepted.

## Date

2026-06-28

## Context

The platform now has governed dbt products, Airflow orchestration and Dataiku ML workflow blueprints. Reusable features need registry, versioning, lineage and point-in-time retrieval without duplicating upstream transformations or prematurely adding online serving.

## Decision

Milestone 12 implements an offline-first feature store. It owns reusable feature definitions, entities, feature views, feature sets, point-in-time retrieval, freshness, validation, lifecycle and Snowflake offline-store contracts.

Dataiku consumes exact feature-set versions and keeps model-specific preprocessing. Online serving is deferred because current use cases are batch-oriented and no sub-second requirement exists.

## Consequences

- Feature reuse becomes explicit and versioned.
- Training and scoring retrieval share the same definitions.
- No Redis, Feast online store or low-latency API is introduced.
- Connected Snowflake materialisation remains future work.

## Validation

- Feature registry static validation.
- dbt parse for curated feature models.
- Deterministic local historical and batch retrieval with checksum verification.
