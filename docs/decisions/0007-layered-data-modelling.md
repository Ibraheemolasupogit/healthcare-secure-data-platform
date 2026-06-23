# ADR 0007: Layered data modelling

- **Status:** Accepted
- **Date:** 2026-06-23

## Context

Source fidelity, reusable logic, governed entities and consumer products have different change and control needs.

## Decision

Adopt RAW, STAGING, INTERMEDIATE, CURATED, MART and SEMANTIC layers with documented grains and dependency direction. Models may depend only on their layer or an earlier layer, except documented utilities.

## Consequences

Lineage and ownership are clearer, at the cost of more relations and the need to avoid pass-through models.

## Alternatives considered

A two-layer warehouse is simpler but mixes concerns. Data Vault is not justified for the initial synthetic source scope.

## Validation

Milestones 5–6 test naming, grain, metadata and dependency rules in CI.
