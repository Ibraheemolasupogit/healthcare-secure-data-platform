# Source ownership

Milestone 5 declares existing source contracts only. It does not invent new raw relations.

| Source group | Snowflake location | Relations | Status |
|---|---|---:|---|
| `raw_clinical` | `HEDP_DEV_RAW.CLINICAL` | 7 | Milestone 2 local fixture, planned RAW relation |
| `raw_operational` | `HEDP_DEV_RAW.OPERATIONAL` | 6 | Milestone 2 local fixture, planned RAW relation |
| `raw_audit` | `HEDP_DEV_RAW.AUDIT` | 2 | local fixture/static contract |
| `raw_interoperability` | `HEDP_DEV_RAW.INTEROPERABILITY` | 2 | Milestone 4 static contract, not deployed |
| `raw_quarantine` | `HEDP_DEV_RAW.QUARANTINE` | 1 | Milestone 4 static contract, not deployed |
| `governance_control` | `HEDP_DEV_GOVERNANCE.CONTROL` | 3 | Milestone 4 static contract, not deployed |
| `governance_data_quality` | `HEDP_DEV_GOVERNANCE.DATA_QUALITY` | 2 | local fixture/static contract |

Snowflake and Terraform retain ownership of databases and schemas. dbt owns declarations, freshness checks, staging SQL, tests, docs, and lineage. Python owns source generation and parser validation.
