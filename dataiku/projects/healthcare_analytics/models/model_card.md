# Billing exception prioritisation model card

Status: blueprint and local reference only. This is not a Dataiku-native model card export.

## Intended use

Support human review of synthetic governed billing and reconciliation exceptions by estimating whether material remediation may be required.

## Prohibited use

Do not use for autonomous clinical decisions, patient treatment, financial posting, write-off automation, regulatory certification, or production prioritisation without approval.

## Data lineage

Trusted inputs are governed dbt outputs: `reconciliation_exception`, `exception_remediation_status`, `revenue_at_risk_summary`, and `billing_exception` lineage where needed.

## Target

`material_remediation_required`, a synthetic local-reference label that is not derived from Milestone 9 priority score or priority band.

## Features and exclusions

Features are model-specific exception attributes such as severity, value at risk, age, recurrence, owner group, source system, payer type, contract type and control status. Excluded leakage fields include priority score, priority band, resolution timestamps, final recovered amount and post-resolution outcomes.

## Split strategy

Deterministic temporal split sorted by `detected_at` and `reconciliation_exception_key`: earliest 70% train, next 15% validation, latest 15% test.

## Algorithms

Baseline: majority-class classifier. Candidate: transparent bounded scorecard. A shallow decision-tree Dataiku visual-ML candidate is specified but not executed locally.

## Metrics

Primary metric: F1. Secondary metrics: precision, recall, confusion matrix, calibration blueprint and top-K metrics blueprint.

## Subgroup assessment

Operational subgroup monitoring covers payer type and source system with a minimum group-size threshold. This is not fairness certification.

## Explainability

Global feature importance is produced by the transparent scorecard. Local explanations are blueprint-only until a live Dataiku implementation exists.

## Human oversight

Finance-control and data-quality roles must review model outputs. No automatic exception action is authorised.

## Monitoring and retraining

Monitor schema validity, missingness, distribution drift, prediction drift, score distribution, calibration when labels arrive, subgroup metrics, stale model age and upstream contract changes. Retraining requires manual approval.

## Synthetic-data statement

All committed inputs and outputs are synthetic. No real patient, financial, employee or credential data is used.
