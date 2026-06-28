# Component responsibilities

| Component | Owns | Does not own | Current status |
|---|---|---|---|
| Snowflake | Persisted layers, warehouses, ingestion primitives, RBAC, policies, sharing, recovery, usage/cost telemetry | Transformation semantics or cross-platform orchestration | Foundation declared and statically validated; not deployed |
| dbt | SQL transformations, source declarations/freshness, tests, contracts, snapshots, docs, lineage, exposures | File transport, BI visuals, user provisioning | M5 sources/staging, M6 healthcare core and M8 billing/finance domain implemented locally; marts planned |
| Python | Synthetic generation, interoperability parsing/mapping, boundary validation and local diagnostics | Warehouse-scale transformations | Generator plus bounded FHIR-inspired/HL7 ingestion and billing/finance source foundation implemented |
| Airflow | Cross-system dependency coordination and recovery | Reimplementing dbt DAGs or Snowflake-local task graphs | Documented placeholder |
| Dataiku | Governed research analysis against approved products | Master transformation layer or uncontrolled export | Workflow/design placeholder |
| Fabric/Power BI | Semantic consumption, measures, operational/executive presentation | Rebuilding curated entities | Consumption placeholder |
| Terraform | Durable Snowflake foundation objects and repeatable environment configuration | Business relations, data transformation or secret storage | DEV/TEST/PROD Snowflake foundation module implemented |
| GitHub Actions | Code quality, security and deployment gates | Runtime orchestration | Credential-free checks |

Ownership prevents duplicated logic: a calculation belongs in dbt when multiple consumers need it; presentation-only measures may remain in the semantic/reporting layer. Snowflake-native scheduling is used when all inputs, actions and recovery are inside Snowflake. Airflow is justified only by an external dependency or cross-system operational need.
