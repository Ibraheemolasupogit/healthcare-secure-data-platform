# Evidence plan

Evidence must be reproducible, dated, environment-labelled, redacted, and traceable to a commit. Never fabricate screenshots or retain sensitive query results.

| Capability | Future evidence | Acceptance signal |
|---|---|---|
| Snowflake deployment | Terraform plan/apply and object inventory | Expected tagged objects exist |
| Warehouse isolation | Role/warehouse matrix and query history | Workloads cannot cross assigned compute |
| RBAC | Positive and negative privilege tests | Least-privilege matrix passes |
| Masking / row access | Same query under controlled roles | Values/rows differ exactly by policy |
| dbt lineage | Manifest/catalog and docs graph | Sources-to-exposures traceable |
| Freshness / tests | dbt artifacts and failing fixture | Gate detects stale/invalid input |
| Snapshots | Before/after SCD fixture | History retained correctly |
| Incremental / microbatch | Idempotence, late-arrival and batch metrics | No duplicates; bounded reprocessing |
| Slim CI | Changed-model selection log | Modified model plus dependants validated |
| Performance | Query profile and benchmark protocol | Repeatable latency/scanning result |
| Cost/usage | Warehouse metering and tagged query report | Cost attributed by workload |
| Streams / Tasks | Change and task history | Exactly expected changes processed/retried |
| Snowpipe | File/load history and duplicate replay | Idempotent ingestion demonstrated |
| Fabric / Power BI | Connection, semantic model and report validation | Approved mart only; refresh succeeds |
| Dataiku | Exported project documentation and scenario log | Governed cohort workflow reproducible |
| GitHub Actions | Protected PR run and release approval | Required gates block an injected failure |

Store text/JSON summaries under `docs/evidence` and large/redacted artefacts outside Git where appropriate, referenced by immutable location and checksum. Screenshots supplement, never replace, machine-readable evidence.
