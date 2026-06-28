# ADR 0012: Healthcare core identity and reconciliation

- **Status:** Accepted
- **Date:** 2026-06-28

## Context

Milestone 6 introduces conformed healthcare core models above source-aligned staging. The core needs stable keys, deterministic identity reconciliation and auditable exceptions without claiming production Master Patient Index capability.

## Decision

dbt owns deterministic synthetic healthcare core identity from Milestone 6 onward. Core models consume Milestone 5 staging models and intermediate reconciliation models only. Surrogate keys use null-safe SHA-256 values derived from canonical business identifiers through an in-project macro. Patient and encounter identity reconciliation uses Milestone 2 canonical IDs plus Milestone 4 crosswalk/envelope evidence. It does not use probabilistic matching.

Reconciliation exceptions are explicit curated outputs for unmatched identifiers, conflicting mappings, orphan relationships and row-count differences. They are not silently filtered out.

## Consequences

Downstream core, billing, analytics, research and ML work has one reusable identity/key strategy. The approach is deterministic and reviewable, but it is not a production MPI or national-reference validation capability.

## Alternatives considered

Database sequences and row-number keys were rejected because they are not stable across reruns. Adding a package for surrogate keys was rejected because a small local macro is sufficient. Probabilistic matching was rejected as out of scope.

## Validation

Milestone 6 static tests enforce one dbt project, no direct `source()` references from core models, no billing/mart/downstream artefacts, documented contracts and SHA-256 key generation.
