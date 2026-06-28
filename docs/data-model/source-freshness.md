# Source freshness

Freshness policies in Milestone 5 are portfolio expectations for synthetic/local contracts. They are not NHS or production clinical standards.

| Source family | Warn after | Error after | Rationale |
|---|---:|---:|---|
| Encounters | 6 hours | 24 hours | Frequent operational activity |
| Appointments and pathways | 12 hours | 36 hours | Scheduling/pathway feeds can be batch-oriented |
| Pathology results | 4 hours | 12 hours | Higher timeliness expectation for lab-like messages |
| Medication events | 6 hours | 24 hours | Clinical event feed expectation |
| FHIR raw payloads | 2 hours | 8 hours | Interoperability payloads are expected to arrive frequently |
| HL7 raw messages | 1 hour | 4 hours | Message feeds are expected to be near-real-time |
| Audit/envelope feeds | 12 hours | 24 hours | Operational audit should remain current |
| Reference/control mappings | 30 days | 90 days | Slowly changing synthetic controls |
| Other source fixtures | 12 hours | 36 hours | Conservative default until connected evidence exists |

Freshness is configured in source YAML and can be overridden with dbt variables for environment-specific database/schema names. Running `dbt source freshness` requires a connected Snowflake target.
