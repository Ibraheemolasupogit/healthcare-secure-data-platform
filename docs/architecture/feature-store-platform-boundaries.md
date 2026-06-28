# Feature-store platform boundaries

| Capability | Owner |
|---|---|
| Canonical entities | dbt healthcare core |
| Billing and finance calculations | dbt billing/finance domain |
| Reconciliation and assurance logic | dbt assurance domain |
| Reusable offline feature definitions | Feature store |
| Model-specific preprocessing | Dataiku |
| Cross-platform triggers | Airflow |
| Online serving | Deferred |
| BI semantic consumption | Milestone 13 |

Feature definitions must use governed models and exact feature-set versions. Dataiku consumes feature sets by reference and keeps only model-specific transformations.
