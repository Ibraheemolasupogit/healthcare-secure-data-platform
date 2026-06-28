# Milestone 13 evidence

Milestone 13 adds a governed Fabric and Power BI consumption foundation.

Evidence summary:

- Workspace blueprints: development, test and production.
- Connectivity decision: Snowflake-to-Power BI Import mode by default; DirectQuery only
  for future approved low-latency requirements; Direct Lake deferred.
- Semantic model count: one shared enterprise model.
- Domains: healthcare operations, billing and finance, revenue assurance and
  data-science outputs.
- Tables: Date, Patient, Organisation, Provider, Payer, Appointments, Encounters,
  Invoices, Payments, Outstanding Balances, Reconciliation Controls, Billing Exceptions
  and Predictions.
- Relationships: explicit, single-direction and statically validated.
- Measures: central catalogue only; no report-local business logic.
- KPIs: source-grounded synthetic portfolio KPIs only.
- Security: RLS and OLS blueprints with no real identities.
- Sensitivity: Microsoft-label mapping documented, not applied.
- Reports: four thin-report specifications with visual-level accessibility metadata.
- Refresh: five refresh groups and incremental-refresh policies documented.
- Deployment: development/test/production promotion blueprint, not deployed.
- Endorsement: process defined; certification not claimed.
- Local reference outputs: generated under `powerbi/reference/`.
- Connected status: Fabric not connected, Power BI not connected, Snowflake not connected.

Limitations:

- No Power BI Desktop, Tabular Editor or Fabric tenant validation was performed.
- No workspaces, datasets, reports, refreshes, dashboards, lakehouses, warehouses,
  notebooks or pipelines were created.
- No real patient, employee, financial, tenant, workspace or credential data was used.

Milestone 14 hand-off: expand security, governance and compliance controls across the
platform without changing Fabric/Power BI ownership of downstream consumption.
