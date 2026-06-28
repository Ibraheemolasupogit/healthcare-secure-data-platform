# Dataiku platform boundaries

| Area | Owner |
|---|---|
| Raw ingestion and interoperability | Snowflake ingestion / existing Python interoperability layer |
| Healthcare core and billing transformations | dbt |
| Reconciliation, priority and value-at-risk controls | dbt Milestone 9 |
| Cross-platform orchestration | Airflow |
| Collaborative analytical workflow and ML design | Dataiku |
| Reusable governed feature store | Milestone 12 |
| Certified semantic reporting | Milestone 13 |

Milestone 11 Dataiku artefacts are blueprints and local reference outputs. They are not Dataiku exports and must not be treated as production execution evidence.
