# dbt documentation and lineage

Milestone 5 source YAML and model YAML provide dbt Docs metadata for sources, staging models, columns, owners, grain, implementation status, freshness, contract maturity, and downstream milestone boundaries.

Credential-free local validation creates a parse manifest under `dbt/target/manifest.json`. Full docs site generation requires a connected Snowflake profile because the Snowflake adapter builds catalog metadata from live relations.

Expected live command:

```bash
cd dbt
dbt docs generate --profiles-dir /secure/profile/path --target dev
dbt docs serve --profiles-dir /secure/profile/path --target dev
```

The lineage graph should show RAW/GOVERNANCE sources feeding only source-aligned staging models in Milestone 5. Core, mart, semantic, Dataiku, Fabric, and feature-store lineage is deferred.
