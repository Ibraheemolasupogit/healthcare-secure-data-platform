# Snowflake foundation architecture

Milestone 3 establishes the minimum secure substrate on which later ingestion and transformation work can land. It is environment-scoped, credential-free to review and explicit about the difference between declared and deployed state.

## Environment topology

DEV, TEST and PROD use identical logical shapes with environment-specific retention, sizing and credit quotas. Every name begins `HEDP_<ENV>_`, preventing accidental cross-environment references. Each environment contains:

| Object | Count | Purpose |
|---|---:|---|
| Databases | 4 | RAW, CURATED, SERVING and GOVERNANCE boundaries |
| Managed schemas | 29 | Domain and control-plane separation without business relations |
| Warehouses | 6 | INGEST, TRANSFORM, QUALITY, RESEARCH, BI and ADMIN isolation |
| Resource monitors | 1 | Monthly environment cost guardrail |
| Account roles | 17 | Five ownership and 12 functional/service roles |
| Tags | 1 | Future sensitivity-class attachment point |

The aggregate committed inventory therefore contains 174 objects. PROD uses longer retention and larger selected warehouses than DEV/TEST, but all warehouses start suspended, auto-resume, auto-suspend within 120 seconds and use bounded statement timeouts. Sizes are cautious starting assumptions, not measured production recommendations.

## Layer and ownership boundaries

RAW is source-aligned and immutable by design; CURATED will hold governed reusable entities; SERVING will expose approved marts and products; GOVERNANCE will hold control, monitoring, security, quality, lineage and evidence metadata. Milestone 3 creates only the containers.

Terraform owns durable platform objects, grants and ownership. dbt will own future business relations and transformation semantics. SQL provides connected validation and evidence queries rather than a second deployment mechanism. This prevents configuration drift between imperative SQL and Terraform state.

`snowflake/config/foundation.json` is the single declarative contract. Terraform decodes it, while the Python package validates references, naming, cycles, dangerous SQL, direct-user grants and inventory consistency. The renderer creates reviewable previews without pretending to be a provider plan.

## Cost and security posture

Workload-specific warehouses prevent research, BI, quality and transformation workloads from competing on one compute pool. An environment resource monitor notifies at 50% and 75%, suspends at 90% and suspends immediately at 100% of quota. Monitoring is a guardrail, not a complete cost-management system.

Managed-access schemas centralise grants. Ownership roles own objects; functional and service roles receive only workload and schema access. No user is provisioned and no object privilege is granted directly to a user. Future read grants apply to tables and views only in explicitly listed schemas.

## Not implemented

No live account deployment, source loading, business table, dbt model, masking policy, row-access policy, network policy, stream, task, share or production benchmark is part of this milestone. The sensitivity tag is an attachment point only and does not imply policy enforcement.
