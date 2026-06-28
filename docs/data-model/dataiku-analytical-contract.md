# Dataiku analytical contract

The primary analytical base table is `billing_exception_priority_analytical_base`.

Grain: one open governed billing or reconciliation exception at prediction time.

Key: `reconciliation_exception_key`.

Target: `material_remediation_required`, a synthetic local-reference label. It is not derived from Milestone 9 `priority_score` or `priority_band`.

Trusted lineage:

- `reconciliation_exception`
- `exception_remediation_status`
- `revenue_at_risk_summary`
- `billing_exception` for lineage context only

The contract excludes leakage fields such as resolution outcomes, final recovered amount, post-resolution root cause, human assignment outcomes and deterministic priority fields.
