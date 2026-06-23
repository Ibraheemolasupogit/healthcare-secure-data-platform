# ADR 0004: Synthetic healthcare data only

- **Status:** Accepted
- **Date:** 2026-06-23

## Context

Portfolio development does not justify processing identifiable or production healthcare data and cannot safely reproduce organisational controls.

## Decision

Accept only clearly labelled, independently generated synthetic records. Prohibit real identifiers, NHS numbers, personal data and production extracts from source, fixtures, logs and evidence.

## Consequences

Development is shareable and lower-risk, but synthetic behaviour cannot prove fitness for clinical or regulatory production use.

## Alternatives considered

De-identified production samples retain re-identification and provenance risk; public health datasets may impose inconsistent terms and realism.

## Validation

Milestone 2 adds provenance labels and invariant tests; every milestone scans fixtures and evidence before commit.
