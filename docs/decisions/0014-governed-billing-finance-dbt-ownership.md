# ADR 0014: Governed billing and finance dbt ownership

## Status

Accepted.

## Context

Milestone 7 created billing and finance source fixtures. The platform now needs one governed place for tariff selection, contract matching, invoice/claim calculations, payment allocation, revenue-event classification and outstanding-balance calculation.

## Decision

dbt owns governed billing and finance calculations from Milestone 8 onward. Milestone 8 publishes source declarations, staging, intermediate calculation paths, curated dimensions, facts and deterministic controls. Python remains the source generator. Snowflake deployment SQL remains infrastructure/platform ownership.

## Consequences

- Tariff, contract, payment allocation and balance logic have one authoritative dbt path.
- Source values and governed values are both preserved.
- Healthcare linkage uses Milestone 6 core models.
- Milestone 9 can build workflows over M8 controls without redefining calculations.

## Alternatives considered

- Keep calculations in Python. Rejected because Python owns source generation, not governed transformation.
- Implement calculations in Snowflake deployment SQL. Rejected because dbt owns transformation logic, contracts and lineage.
- Defer all billing transformations to Milestone 9. Rejected because Milestone 9 needs governed financial outputs to reconcile.
