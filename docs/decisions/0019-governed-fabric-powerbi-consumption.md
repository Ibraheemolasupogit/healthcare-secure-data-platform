# ADR 0019: Governed Fabric and Power BI consumption

Status: Accepted  
Date: 2026-06-28

## Context

The platform now has governed ingestion, Snowflake, dbt, assurance, Airflow, Dataiku and
feature-store foundations. Downstream consumers need a governed semantic and reporting
layer without duplicating upstream transformations or creating live tenant dependencies.

## Decision

Use Microsoft Fabric and Power BI as a downstream consumption layer only. Define one
shared enterprise semantic model, centralised measures and KPIs, RLS/OLS blueprints,
sensitivity mapping, thin-report specifications, refresh strategy and deployment pipeline
blueprint.

Power BI consumes governed dbt, Dataiku and feature-store contracts. It must not recreate
healthcare entities, billing totals, finance balances, reconciliation logic, value-at-risk,
model features or model thresholds.

Import mode is the default storage pattern for this local-first foundation. DirectQuery is
reserved for future low-latency requirements. Direct Lake is deferred until a governed
Fabric-native storage design exists.

## Consequences

- Semantic model definitions and report specifications are source-controlled and
  credential-free.
- Reports remain thin and inherit central measures and security.
- No Fabric deployment, workspace creation, dataset publication, refresh, certification or
  tenant evidence is claimed.
- Future deployment can bind the metadata to real tenant resources after security and
  governance controls are expanded.

## Alternatives considered

- PBIX binaries in the repository: rejected because they are opaque and not locally
  validateable.
- Fabric lakehouse duplication: rejected because Snowflake/dbt remains authoritative.
- DirectQuery by default: rejected because no low-latency requirement exists.
- Report-level measures: rejected because they fragment business truth.

## Validation

Repository validation checks model metadata, sources, relationships, measures, KPIs,
security roles, OLS rules, report specifications, accessibility metadata, refresh
policies, deterministic reference outputs, checksums and future-scope prohibitions.
