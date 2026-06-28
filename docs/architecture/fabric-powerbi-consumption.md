# Fabric and Power BI consumption architecture

Milestone 13 adds a governed consumption layer after the governed offline feature store.
Fabric and Power BI consume trusted Snowflake/dbt, Dataiku and feature-store outputs;
they do not recreate upstream healthcare, billing, reconciliation, feature or model
logic.

The default pattern is:

```text
governed Snowflake/dbt products
→ consumption contracts
→ one shared Power BI semantic model
→ central measures, KPIs, RLS and OLS
→ thin reports
→ future Fabric/Power BI deployment pipeline
```

The repository contains metadata blueprints only. No Fabric tenant, capacity, workspace,
pipeline, lakehouse, notebook, Power BI dataset, report publication, refresh history or
certification status is claimed.

Import mode is the default storage-mode decision. It is sufficient for the deterministic
synthetic portfolio, limits Snowflake interactive compute exposure, and preserves semantic
model flexibility. DirectQuery is reserved for an approved low-latency requirement. Direct
Lake is deferred until a governed Fabric-native storage design exists.
