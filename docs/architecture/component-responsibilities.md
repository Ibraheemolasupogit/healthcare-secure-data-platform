# Component responsibilities

| Component | Owns | Does not own | Current status |
|---|---|---|---|
| Snowflake | Persisted layers, warehouses, ingestion primitives, RBAC, policies, sharing, recovery, usage/cost telemetry | Transformation semantics or cross-platform orchestration | Modular design scaffolding only |
| dbt | SQL transformations, source declarations/freshness, tests, contracts, snapshots, docs, lineage, exposures | File transport, BI visuals, user provisioning | Valid project skeleton and conventions |
| Python | Synthetic generation, boundary validation, ingestion helpers, local diagnostics | Warehouse-scale transformations | Generator, schemas, writers, validation and CLI implemented; ingestion helpers planned |
| Airflow | Cross-system dependency coordination and recovery | Reimplementing dbt DAGs or Snowflake-local task graphs | Documented placeholder |
| Dataiku | Governed research analysis against approved products | Master transformation layer or uncontrolled export | Workflow/design placeholder |
| Fabric/Power BI | Semantic consumption, measures, operational/executive presentation | Rebuilding curated entities | Consumption placeholder |
| Terraform | Repeatable resource configuration across environments | Data transformation or secret storage | Provider/module/environment scaffold |
| GitHub Actions | Code quality, security and deployment gates | Runtime orchestration | Credential-free checks |

Ownership prevents duplicated logic: a calculation belongs in dbt when multiple consumers need it; presentation-only measures may remain in the semantic/reporting layer. Snowflake-native scheduling is used when all inputs, actions and recovery are inside Snowflake. Airflow is justified only by an external dependency or cross-system operational need.
