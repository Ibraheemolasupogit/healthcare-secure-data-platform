# Target production architecture

## Environments and isolation

Development, test and production use separate databases and preferably separate accounts for strong administrative isolation. Within an environment, warehouses isolate ingestion, engineering, BI and research workloads. Resource monitors, auto-suspend, statement timeouts, tagging and query history support cost governance.

Object ownership roles are separated from functional access roles. Service identities use key-pair or workload-identity authentication with rotation; humans use federated SSO and MFA. Network policies and private connectivity are evaluated for production.

## Data path

Object storage notifications feed Snowpipe for eligible sources; controlled batch `COPY` supports replay. RAW retains payload and provenance. dbt produces governed downstream layers. Streams expose changes and Tasks execute Snowflake-local processing. Secure views/shares or governed connectors expose only approved products.

Research access is project-, purpose-, cohort- and time-bound. Dataiku operates inside that approval boundary. Fabric/Power BI connect with read-only service roles to semantic products. Exports are logged, reviewed and limited.

## Operations

Terraform manages durable infrastructure. Promotion uses reviewed plans and protected environments. dbt artifacts, tests, freshness, Snowflake access/query history, load errors, task history and cost telemetry flow to monitoring. Recovery uses replayable RAW data, Time Travel, clones and documented restoration tests.

None of this production topology is deployed in Milestones 1–2.
