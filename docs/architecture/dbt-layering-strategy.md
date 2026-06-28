# dbt layering strategy

Milestone 5 makes the existing dbt project the authoritative transformation boundary without starting conformed modelling.

The allowed dependency direction is:

```text
RAW sources -> STAGING -> future INTERMEDIATE -> future CURATED -> future MART -> future SEMANTIC
```

## Milestone 5 scope

Implemented now:

- dbt sources for existing Milestone 2 synthetic datasets and Milestone 4 interoperability contracts.
- Source freshness metadata on every declared source relation.
- Source-aligned staging views under `dbt/models/staging`.
- Staging utility macros for empty-string normalisation, code casing, safe casts, and deterministic deduplication.
- Source and staging documentation, data tests, and static Python guardrail tests.

Not implemented now:

- conformed patients, providers, organisations, encounters, appointments, pathways, facts, dimensions, marts, semantic models, billing, revenue, reconciliation, feature definitions, BI artefacts, or orchestration.

## Ownership

Snowflake owns durable RAW and GOVERNANCE containers. dbt owns source declarations, staging transformations, tests, documentation, lineage, and future governed transformations. Python keeps owning synthetic generation and interoperability parsing. Downstream tools must consume dbt-owned products rather than duplicate transformation logic.

## Local versus live execution

Credential-free CI parses the dbt graph and statically validates source/staging boundaries. `dbt compile`, `dbt build`, `dbt source freshness`, and `dbt docs generate` require a real Snowflake target because this project intentionally uses the Snowflake adapter rather than adding a second warehouse runtime.
