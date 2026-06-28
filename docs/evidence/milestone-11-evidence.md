# Milestone 11 evidence

Milestone 11 adds a governed Dataiku analytics and MLOps blueprint.

## Selected use case

Billing exception prioritisation over trusted governed billing and assurance outputs.

## Implemented inventory

- Dataiku project blueprint.
- Acyclic Flow specification.
- Trusted input contracts.
- Analytical base-table contract.
- Feature specification.
- Recipe specifications.
- Experiment, evaluation and approval-gate specifications.
- Training, scoring and monitoring scenario blueprints.
- Model registry blueprint and model card.
- Prediction-output contract.
- Deterministic local reference fixture and outputs.
- Static guardrail tests in `tests/unit/test_dataiku_milestone11.py`.

## Local reference status

The local reference pipeline is not Dataiku-produced, not Snowflake-connected, not deployed and not production-approved.

## Milestone 12 hand-off

Milestone 12 should implement a governed feature-store layer for reusable, versioned, point-in-time-correct features. Milestone 11 only marks reusable feature candidates.
