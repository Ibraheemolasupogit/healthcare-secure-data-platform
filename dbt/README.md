# dbt foundation

This is a parseable skeleton, not an implemented transformation project. No fake domain models are included.

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

`dbt parse --profiles-dir . --no-partial-parse` validates structure without connecting to Snowflake. The placeholder profile must never be used for execution.
