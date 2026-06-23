# ADR 0001: Snowflake as the primary data platform

- **Status:** Accepted
- **Date:** 2026-06-23

## Context

The target needs separated storage/compute, isolated workloads, governed sharing, native ingestion/change processing, strong access policies, recovery and measurable cost controls.

## Decision

Use Snowflake as the authoritative persisted platform. Use warehouses by workload and Snowflake-native RBAC, policies, Snowpipe, Streams/Tasks, Time Travel, cloning, sharing and usage telemetry where their milestones require them.

## Consequences

The project gains practical depth and coherent controls but accepts platform-specific SQL, external-service cost and the need for real Snowflake integration tests. Portable contracts and transformation intent limit unnecessary coupling.

## Alternatives considered

PostgreSQL improves local parity but does not demonstrate the target native capabilities. A multi-warehouse abstraction would dilute depth and increase unvalidated complexity.

## Validation

Milestones 3, 8–10 must deploy and test controls in an isolated account and capture evidence.
