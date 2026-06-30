# ADR 0023: Metadata-first operational observability

## Status

Accepted

## Context

The platform needs operational-readiness evidence without deploying live
monitoring, alerting or incident-response integrations.

## Decision

Use repository-managed metadata for service health, SLIs, synthetic SLO targets,
incident classification, alert-routing blueprints, runbook linkage and local
recovery-drill simulation.

All live alerting, SIEM, ticketing, on-call, dashboard, cloud-monitoring,
automatic remediation, live failover and production SLO enforcement remain out
of scope.

## Consequences

The repository can validate operational readiness deterministically and without
credentials. Production monitoring and live response integrations require a
future explicit milestone.
