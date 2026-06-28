# Staging model conventions

Milestone 5 staging models are thin, source-aligned views named `stg_<domain>__<source_relation>`. They preserve source identifiers and lineage and do not create conformed healthcare entities.

## Required pattern

Each staging model:

- selects from exactly one `source()` relation;
- explicitly casts dates, timestamps, booleans, and numeric values where the source contract provides a type;
- trims empty strings to null for text fields;
- uppercases controlled status/code fields without reinterpreting clinical meaning;
- preserves the source primary key and derives `source_record_id` from it;
- adds `source_relation`, `source_updated_at` where grounded, `dbt_loaded_at`, `dbt_invocation_id`, `synthetic_flag`, and `is_duplicate`;
- applies deterministic deduplication using the documented source key and source update or receive timestamp;
- avoids joins, aggregations, facts, dimensions, marts, billing logic, and conformed surrogate keys.

## Contract maturity

Staging interfaces are documented with dbt contract metadata, but `enforced: false` because the raw sample contracts are still local/static and live Snowflake relations are not deployed. Enforcement can be switched on after a connected Snowflake environment proves the physical column types.
