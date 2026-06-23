# ADR 0006: Separate transformation from reporting

- **Status:** Accepted
- **Date:** 2026-06-23

## Context

Business rules embedded independently in dashboards drift and are hard to test or reuse.

## Decision

Conformed entities and reusable metrics are produced by dbt and exposed through governed semantic interfaces. Fabric/Power BI own presentation, interaction and genuinely report-specific measures only.

## Consequences

Consumers share definitions and lineage. Some presentation measures still need explicit ownership and regression checks.

## Alternatives considered

BI-centric modelling is quick initially but duplicates logic; a separate semantic platform is premature for this scope.

## Validation

Milestone 13 traces each report element to a semantic interface and records any approved report-local calculation.
