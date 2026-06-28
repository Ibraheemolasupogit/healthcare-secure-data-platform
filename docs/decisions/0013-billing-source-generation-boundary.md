# ADR 0013: Billing source generation boundary

## Status

Accepted.

## Context

The platform roadmap needs billing and finance data before dbt billing transformations can be implemented. Combining source generation with downstream finance logic would make it unclear whether validation failures belong to source contracts or transformation semantics.

## Decision

Milestone 7 implements billing and finance as deterministic synthetic source records in the existing generator only. Decimal-safe source arithmetic, lifecycle chronology, manifests, checksums and negative fixtures are included. dbt billing transformations and governed finance products are deferred.

## Consequences

- Milestone 8 can build dbt billing logic against stable source fixtures.
- Source validation remains fast and credential-free.
- The repository can demonstrate financial controls without claiming accounting-policy implementation.
- Downstream revenue recognition, allocation and mart reconciliation remain explicit future work.

## Alternatives considered

- Implement billing dbt models in the same milestone. Rejected because it mixes source and transformation ownership.
- Create a second billing generator. Rejected because it would duplicate profile, manifest and validation conventions.

