# ADR 0009: Expand to a healthcare enterprise data platform

- **Status:** Accepted
- **Date:** 2026-06-23

## Context

Milestones 1–2 established a Snowflake/dbt-centred secure healthcare platform foundation and deterministic clinical/operational synthetic sources. The target now includes interoperability, healthcare billing and finance, reconciliation, Dataiku analytics/ML, a governed feature store, Fabric/Power BI consumption, broader infrastructure automation and multi-region operations. A broad expansion risks duplicating working patient/encounter models, business calculations and technology responsibilities.

## Decision

Expand the target architecture while preserving the current implementation and its Snowflake/dbt centre of gravity. Extend one synthetic package, one versioned schema catalogue, one dbt project and one Snowflake deployment structure. Introduce new capabilities only at dependency-led milestone boundaries and label target-state assets separately from implemented evidence.

Responsibilities remain explicit: FHIR/HL7 validate and map source messages; Snowflake governs storage, compute and access; dbt owns transformations and shared business logic; Airflow coordinates cross-platform work; Dataiku consumes trusted products for analytics/ML; the feature store governs reusable features; Fabric/Power BI own semantic consumption/reporting; Terraform provisions infrastructure; governance, security, quality, observability and CI/CD span all components.

## Preservation and non-cannibalisation constraints

The existing generators, schema versions, identifier rules, code sets, profiles, validation, CLI, manifests/checksums, samples, tests, documentation, ADRs, workflows, dbt project, Snowflake structure, Terraform module/environment pattern and Docker path remain authoritative extension points. No new patient, encounter, generator, dbt-project or deployment root may be added merely to match a target diagram. Moves and breaking schema/CLI changes require a separate migration decision and compatibility plan.

## Alternatives considered

- Recreate the repository as an enterprise skeleton: rejected because it destroys evidence and replaces working capability with placeholders.
- Add every technology immediately: rejected because empty integrations exaggerate status and obscure dependency order.
- Keep the original clinical-only scope: rejected because it cannot demonstrate billing/revenue assurance or governed analytical/ML consumption.
- Put business logic in Dataiku or BI tools: rejected because definitions would fragment outside dbt lineage and tests.

## Consequences

The roadmap grows from 15 to 17 milestones and redistributes previous ingestion, quality, security, CI and evidence work. Billing synthetic sources become a focused M7 extension immediately before billing dbt models, avoiding retroactive changes to completed M2. Delivery takes longer, but ownership, provenance and validation remain intelligible. Existing placeholder directories continue to be described honestly.

## Implementation sequence and deferred capabilities

Proceed with Snowflake foundation, interoperability, dbt staging/core, billing source extension, billing dbt/reconciliation, Airflow, Dataiku, feature store, Fabric/Power BI, executable governance, broader Terraform, multi-region/runbooks and final evidence—in that order. Online feature serving, real clinical interfaces, production credentials/data, cloud deployment and compliance certification remain deferred until their prerequisites and authorisation exist.

## Validation expectations

Every milestone must preserve existing imports, CLI contracts, deterministic sample checksums unless a documented schema/version change requires regeneration, and all credential-free gates. New domain definitions require explicit grain/owner/key tests. Cross-platform consumers must trace to dbt-owned products. Architectural claims require reproducible evidence; placeholders never satisfy implementation acceptance.
