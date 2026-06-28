# Feature-store foundation

Milestone 12 adds an offline-first governed feature-store foundation.

The feature store owns reusable feature metadata, entity and join-key definitions, feature-view definitions, feature-set composition, point-in-time retrieval rules, freshness, validation, lineage, lifecycle and Snowflake offline-store mapping.

It consumes trusted dbt outputs from Milestones 6, 8 and 9. It does not own raw ingestion, healthcare entities, billing calculations, reconciliation logic, Dataiku experiments, Airflow orchestration, online serving or BI reporting.

Online serving is deferred because current use cases are batch-oriented and do not have sub-second latency, throughput or availability requirements.
