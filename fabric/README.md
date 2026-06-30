# Microsoft Fabric consumption blueprint

Milestone 13 defines a repository-managed Microsoft Fabric and Power BI consumption
foundation. The artefacts in this directory are local metadata blueprints only: no
Fabric tenant, workspace, capacity, gateway, pipeline, lakehouse, warehouse, notebook,
or refresh job has been created.

Fabric owns consumption topology, workspace governance, connection patterns, deployment
promotion and endorsement workflow. It does not own ingestion, dbt transformations,
Dataiku workflows, governed feature definitions or Airflow orchestration.

## Local artefacts

- `workspaces/` defines synthetic-only development, test and production workspace
  blueprints.
- `connections/` documents the credential-free Snowflake connectivity contract.
- `deployment/` describes promotion stages, gates, rollback and evidence capture.
- `governance/` maps endorsement, certification and sensitivity-label expectations.
- `validation/` records static validation rules used by the repository checks.

## Status

All Fabric artefacts are `blueprint_only`. They are not tenant validated, not deployed,
not refreshed and not certified.

Milestone 14 maps workspace roles, sharing, sensitivity and refresh identity expectations
to the central governance registry. No live tenant security configuration is performed.

Milestone 15 deployment controls require workspace/artefact versioning, environment
approval, connection rebinding evidence, refresh validation evidence and rollback
references before any live Fabric promotion. No tenant deployment is performed.

Milestone 16 recovery controls document workspace recreation, connection rebinding,
sensitivity restoration and refresh-disabled-until-validated behaviour. No tenant recovery
is performed.
## Milestone 17 operations boundary

Operational readiness consumes Fabric/Power BI semantic-model, relationship,
measure, KPI, RLS/OLS and refresh-contract metadata as local health checks. It
does not call Fabric or Power BI APIs or create live refresh alerts.
