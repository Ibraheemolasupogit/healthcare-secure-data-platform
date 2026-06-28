# Governed healthcare feature store

Milestone 12 implements an offline-first feature-store foundation.

The feature store owns reusable feature metadata, entity join keys, feature-view definitions, feature-set composition, point-in-time retrieval rules, freshness, validation, lineage, lifecycle and Snowflake offline-store mapping.

It does not own raw ingestion, healthcare entity definitions, billing calculations, assurance calculations, Dataiku experiments, Airflow orchestration, online serving or BI reporting.

Current scope:

- registry YAML files under `registry/`;
- static contracts under `contracts/`;
- deterministic local reference retrieval under `reference/`;
- curated dbt feature-model blueprints under `dbt/models/curated/features`.

Online serving is explicitly deferred.

Milestone 13 consumes feature-set version metadata in Power BI specifications. It does not move reusable feature ownership into Fabric or Power BI.

Milestone 14 governance mapping validates feature owners, sensitivity, approved consumers,
purpose, point-in-time rules, lifecycle, export classification, retention and model
lineage. Online serving remains deferred.
