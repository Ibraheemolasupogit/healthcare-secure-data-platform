# Semantic-model boundaries

The Power BI semantic model owns business-friendly names, relationships, display folders,
hierarchies, perspectives, measures, KPIs, RLS, OLS and report-facing metadata.

It does not own:

- raw ingestion or cleansing;
- dbt entity, billing, finance or assurance calculations;
- Dataiku model training or thresholds;
- governed feature definitions;
- Airflow scheduling;
- infrastructure provisioning.

Allowed transformations are limited to presentation and semantic-layer concerns:
renaming, hiding technical fields, formatting, relationships, central measures, display
folders, hierarchies, perspectives and security roles.

Prohibited transformations include tariff matching, financial recalculation, patient
identity resolution, exception reprioritisation, feature recomputation, raw cleansing and
model retraining.
