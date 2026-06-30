# dbt foundation

This now contains the Milestone 5 source/staging foundation, the Milestone 6 conformed healthcare core, the Milestone 8 governed billing/finance domain, the Milestone 9 assurance-control layer, and Milestone 12 offline feature-view models. It remains intentionally bounded: no marts, semantic models, external workflows, online feature serving or downstream BI logic are included.

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

Implemented Milestone 8 assets:

- 18 billing/finance source declarations and source-aligned staging views;
- tariff and contract matching, invoice/claim calculations, payment allocation, revenue-event classification, outstanding-balance and control intermediates;
- payer, service, product, tariff and contract dimensions;
- billable activity, claim, invoice, payment, refund, adjustment, revenue-event and outstanding-balance facts;
- billing exception and finance daily-control models;
- billing/finance guardrail tests and documentation.

Implemented Milestone 9 assets:

- tolerance, ownership, severity, lifecycle and priority rule seeds;
- reconciliation control results over Milestone 8 controls and facts;
- consolidated exception inventory, lifecycle events and remediation status;
- revenue-at-risk, daily assurance, month-end assurance and evidence-pack models;
- assurance guardrail tests and deterministic local evidence-pack CLI.

Implemented Milestone 12 assets:

- curated offline feature-view models under `models/curated/features`;
- reusable exception, reconciliation, payer and appointment feature views;
- registry-linked contracts and guardrail tests;
- dbt parse validation without live Snowflake materialisation.

Milestone 14 governance mapping references curated and externally consumed dbt models for
owner, sensitivity, contract status, lineage, retention and export-policy coverage. dbt
continues to own transformation logic and model grains.

Milestone 15 deployment controls require dbt parse/static checks in pull requests, exact
manifest checksum continuity for connected promotion, and protected approval before any
connected dbt build. No connected dbt execution is added here.

`dbt parse --profiles-dir . --no-partial-parse` validates structure without connecting to Snowflake. The placeholder profile must never be used for execution. Connected `dbt compile`, `dbt build`, `dbt source freshness` and `dbt docs generate` require a separate authorised Snowflake profile.
