# Healthcare core model

Milestone 6 adds the conformed healthcare core above Milestone 5 staging. The core standardises shared healthcare concepts once so later billing, research, analytics and ML milestones can reuse them.

Implemented core entities:

- patient identity
- patient
- organisation
- location
- provider
- encounter
- admission
- appointment
- pathway
- clinical event
- pathology result
- medication event
- consent
- research eligibility foundation
- reconciliation exceptions and row-count reconciliation

The core models live under `dbt/models/curated/core`. They use `ref()` dependencies only and never read raw sources directly.

## Boundary

Implemented:

- deterministic synthetic identity reconciliation
- SHA-256 surrogate keys
- conformed current-state core entities
- source lineage fields
- declared contracts and tests
- reconciliation exception outputs

Deferred:

- billing and finance entities
- marts and semantic models
- production MPI
- national reference-data validation
- Airflow, Dataiku, Fabric, Power BI and feature-store work

## Execution status

The graph is credential-free parseable and statically validated. Runtime dbt build, tests and docs generation require an authorised Snowflake target.
