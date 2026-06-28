# ADR 0015: Assurance layer owns reconciliation, not finance calculation

## Status

Accepted.

## Date

2026-06-28

## Context

Milestone 8 established governed billing and finance dbt outputs. Milestone 9 needs reconciliation, exception lifecycle, prioritisation, remediation state and revenue-at-risk evidence without duplicating the upstream finance logic.

## Decision

Milestone 9 introduces an assurance layer that consumes Milestone 8 outputs through dbt `ref()` and rule seeds. It owns assurance status, exception lifecycle, ownership, priority, value-at-risk grouping and evidence-pack metadata.

Milestone 9 does not own tariff selection, contract matching, claim or invoice amount calculation, payment allocation, revenue-event classification or outstanding-balance calculation.

## Consequences

- Assurance logic can evolve without changing source or finance calculation ownership.
- Static guardrails can detect raw-source access or later-platform scope creep.
- Connected runtime validation is deferred until authorised Snowflake credentials are available.

## Alternatives considered

- Put assurance logic inside the M8 finance models. Rejected because it would mix calculation ownership with operational control workflow.
- Build assurance as BI/marts first. Rejected because semantic and reporting layers are later milestones.

## Validation

- `dbt parse --profiles-dir . --no-partial-parse`.
- `PYTHONPATH=src pytest tests/unit/test_dbt_milestone9.py`.
- Deterministic local evidence-pack generation.
