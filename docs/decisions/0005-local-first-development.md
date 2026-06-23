# ADR 0005: Local-first development

- **Status:** Accepted
- **Date:** 2026-06-23

## Context

Contributors need fast, reproducible feedback without permanent cloud credentials, while Snowflake-specific features still require authentic testing.

## Decision

Run unit/static/structural checks locally and in credential-free CI. Use Docker for reproducibility and protected ephemeral Snowflake integration environments only where semantics require them.

## Consequences

Most feedback is cheap and fast. Local success is not treated as proof of Snowflake behaviour; integration gates remain mandatory later.

## Alternatives considered

Cloud-only development is costly and credential-heavy. Emulating every Snowflake feature locally creates false confidence.

## Validation

Milestone 1 validates the local scaffold; later milestones maintain a documented local/cloud test matrix.
