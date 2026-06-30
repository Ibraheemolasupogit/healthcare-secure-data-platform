# ADR 0022: Active/passive recovery strategy

## Status

Accepted, 2026-06-30.

## Context

The platform has local governance, deployment controls and evidence, but no live
multi-region infrastructure. Recovery design must preserve Terraform, governance and
deployment ownership while avoiding false resilience claims.

## Decision

Use a symbolic active/passive warm-standby recovery design with manual failover and manual
failback. Recovery begins with governance and deployment controls, then restores
infrastructure contracts, Snowflake, dbt products, assurance, orchestration, feature store,
Dataiku and Fabric/Power BI in dependency order.

RTO/RPO targets are synthetic portfolio targets and not production commitments. Local
simulation validates metadata and sequencing only.

## Consequences

The repository can test recovery design deterministically without cloud credentials. Future
live exercises must add authorised regions, protected approvals, evidence capture and
clear limitations.

## Alternatives considered

- Active-active design: rejected as unnecessary breadth without live service evidence.
- Automatic failover/failback: rejected because approval, policy integrity and data
  reconciliation must be proven first.
- Duplicating Terraform roots: rejected because Milestone 3 remains infrastructure owner.

## Validation

Validation uses registry checks, dependency graph checks, deterministic simulation,
recovery manifests and checksum evidence.

