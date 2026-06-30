# Operational observability architecture

Milestone 17 defines operational observability as local metadata contracts plus
deterministic simulation.

The operational layer consumes existing platform metadata:

- Milestone 10 orchestration metadata for pipeline health.
- Milestone 14 governance metadata for audit events and policy boundaries.
- Milestone 15 deployment evidence for drift, rollback and promotion health.
- Milestone 16 recovery metadata for tiers, RTO/RPO targets and drill ordering.

The layer owns service catalogue metadata, health state calculation,
SLI/SLO definitions, incident classification, routing metadata, runbook links,
drill catalogue entries and generated evidence.

It does not deploy a monitoring stack or connect to production systems.
