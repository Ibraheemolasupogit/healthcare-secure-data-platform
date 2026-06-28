# dbt foundation

This now contains the Milestone 5 source/staging foundation and the Milestone 6 conformed healthcare core. It remains intentionally bounded: no billing, finance, marts, semantic models or downstream-platform logic are included.

Models follow `stg_<source>__<entity>`, `int_<domain>__<purpose>`, `dim_<entity>`, `fct_<event>`, `mart_<domain>__<purpose>` and `sem_<subject>` naming. Each published model will document owner, description, grain, classification, allowed use, columns and upstream assumptions. SQL uses lower-case keywords and explicit column lists.

STAGING maps one source relation; INTERMEDIATE holds reusable logic; CURATED owns governed facts/dimensions; MARTS serve use cases; SEMANTIC provides stable consumption interfaces and exposures. Cross-layer references move forward only.

Future strategy:

- **Contracts:** enforce on CURATED/MART/SEMANTIC after schemas stabilise; breaking changes use model versions and migration windows.
- **Tests:** source freshness, keys/relationships/accepted values, healthcare invariants, unit tests for logic, and reconciliation at publication boundaries.
- **Incremental:** require unique key, documented watermark, late-arrival window, idempotency and full-refresh equivalence tests.
- **Microbatch:** reserve for time-series event facts at demonstrated volume; record batch window and recovery behaviour.
- **Snapshots:** use timestamp strategy when reliable, check strategy otherwise; record grain and invalidation policy.
- **Slim CI:** defer until a trusted production manifest exists; run state-modified models plus downstream dependants in an isolated schema.
- **Ownership:** every model has an accountable owner; CODEOWNERS and metadata enforcement arrive with implemented models.

Implemented Milestone 5 assets:

- 23 source declarations across clinical, operational, audit, interoperability, quarantine and governance source groups.
- Freshness metadata for every declared source relation.
- 23 source-aligned staging views under `models/staging`.
- Generic tests and staging macros for key uniqueness, checksum validation, safe casts, code normalisation and deterministic deduplication.
- Model documentation and contract metadata with enforcement deferred until live Snowflake column types are proven.

Implemented Milestone 6 assets:

- deterministic synthetic patient and encounter identity reconciliation;
- conformed patient, organisation, location, provider, encounter, admission, appointment, pathway, clinical event, pathology result, medication event and consent models;
- research eligibility foundation and core reconciliation outputs;
- SHA-256 surrogate-key macro and core guardrail tests.

`dbt parse --profiles-dir . --no-partial-parse` validates structure without connecting to Snowflake. The placeholder profile must never be used for execution. Connected `dbt compile`, `dbt build`, `dbt source freshness` and `dbt docs generate` require a separate authorised Snowflake profile.
