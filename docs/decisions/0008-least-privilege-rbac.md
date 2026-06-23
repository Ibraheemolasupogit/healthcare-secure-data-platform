# ADR 0008: Least-privilege role-based access control

- **Status:** Accepted
- **Date:** 2026-06-23

## Context

Healthcare workloads require distinct administrative, engineering, analytical, research and service permissions.

## Decision

Use object ownership roles feeding functional roles; grant roles to identities and avoid direct object grants. Default deny, separate duties, constrain researchers by purpose/cohort/time, and test allowed and denied actions.

## Consequences

Role design and automated entitlement tests become first-class infrastructure. More roles add management overhead but make privilege review intelligible.

## Alternatives considered

Broad shared roles are simpler but create excessive privilege. Per-user grants are difficult to audit and revoke consistently.

## Validation

Milestones 3 and 9 deploy a role matrix and execute positive/negative access tests under each persona.
