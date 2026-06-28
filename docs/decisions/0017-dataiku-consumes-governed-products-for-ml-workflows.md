# ADR 0017: Dataiku consumes governed products for ML workflows

## Status

Accepted.

## Date

2026-06-28

## Context

The platform now has governed dbt entities, billing and assurance models plus Airflow orchestration. Milestone 11 needs collaborative analytics and ML workflow design without replacing these owners.

## Decision

Dataiku consumes trusted governed dbt outputs and owns analytical Flow design, model-specific feature preparation, experiments, evaluation, documentation, approval gates, scenario blueprints, scoring design and monitoring design.

Dataiku does not own raw ingestion, canonical healthcare entities, finance calculations, reconciliation/priority logic, Airflow orchestration, feature-store definitions, semantic reporting or production approval.

Repository artefacts are blueprints and local reference evidence unless a live Dataiku instance is explicitly used and separately evidenced.

## Consequences

- Dataiku remains useful without a licence or live instance.
- Local reference execution can test governance and leakage controls.
- Feature-store ownership remains deferred to Milestone 12.

## Validation

- `PYTHONPATH=src pytest tests/unit/test_dataiku_milestone11.py`.
- Deterministic local reference execution and checksum verification.
- Existing credential-free validation gates.
