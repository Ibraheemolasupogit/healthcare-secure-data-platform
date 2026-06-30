# Power BI governed consumption layer

Milestone 13 defines a local, repository-owned Power BI consumption foundation over
trusted Snowflake/dbt, Dataiku and feature-store products. It uses YAML and JSON
metadata so the repository remains useful without Power BI Desktop, Tabular Editor,
a Fabric tenant or a live Snowflake connection.

The implementation follows a thin-report pattern:

- one shared enterprise semantic model;
- centralised relationships, measures, KPIs, RLS and OLS;
- report specifications without PBIX binaries;
- no Power Query business transformations;
- no report-level business truth.

All artefacts are metadata only, synthetic-only, not published, not refreshed, not
tenant validated and not certified.

Milestone 14 maps RLS, OLS, sensitivity, export, certification and model-output controls
to the central governance registry. Power BI does not own independent governance truth.

Milestone 15 deployment controls require semantic model, measure, KPI, RLS/OLS,
sensitivity, report and accessibility validation before promotion. No Power BI service
publication, refresh or certification is performed.

Milestone 16 recovery controls restore semantic-model metadata, reports, RLS/OLS and
sensitivity mapping before refresh is re-enabled. No Power BI service recovery is
performed.
