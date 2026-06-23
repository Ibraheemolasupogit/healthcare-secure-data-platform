# Solution overview

## Current state

Milestone 1 implements repository structure, decision records, standards, a diagnostic Python CLI, and non-production scaffolding. It creates no data platform resources and processes no health records.

## Target flow

1. Python produces explicitly synthetic batch and semi-structured fixtures at configurable scale.
2. Snowflake stages and Snowpipe ingest immutable payloads into RAW; load metadata supports replay and audit.
3. dbt builds STAGING, INTERMEDIATE, CURATED, MART, and SEMANTIC products with tests, contracts, documentation and lineage.
4. Snowflake policies enforce role- and row-aware access; isolated warehouses separate engineering, BI, research and service workloads.
5. Snowflake Streams/Tasks handle platform-local change processing. Airflow coordinates only dependencies that cross platform boundaries.
6. Approved researchers use governed Dataiku projects; Fabric and Power BI consume published semantic interfaces.
7. Monitoring combines dbt artifacts, Snowflake usage/access history, quality events, orchestration signals and CI evidence.

Snowflake is authoritative for governed persisted data and platform controls. dbt is authoritative for transformation definitions. Python is not a parallel transformation engine, and reporting tools do not own business logic.

## Trust boundaries

Source landing, platform administration, transformation, governed consumption, research workspaces and downstream exports are separate trust zones. Direct identifiers will be isolated from pseudonymised analytical data. Export is an explicit controlled action, not an implied consequence of query access.

## Portability

SQL models, Python generators, data contracts, naming standards and test intent remain portable where practical. Snowflake-native capabilities are intentionally used where they supply material security, operational or economic value. Interfaces and responsibilities are documented so another implementation can replace a component without silently changing semantics.
