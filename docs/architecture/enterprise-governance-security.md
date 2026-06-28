# Enterprise governance and security foundation

Milestone 14 creates one central governance-policy registry for the synthetic healthcare
platform. It defines classifications, sensitivity levels, data domains, personas,
purposes, access policies, consent-aware controls, masking, row/object access, export,
retention, audit events, service identities and control mappings.

The registry maps to existing platform owners rather than replacing them:

- Snowflake M3 remains authoritative for roles, tags, grants and Terraform ownership.
- dbt M5–M12 remains authoritative for transformation logic and model grains.
- Airflow M10 remains authoritative for orchestration.
- Dataiku M11 remains authoritative for model workflows.
- Feature store M12 remains authoritative for reusable feature definitions.
- Fabric/Power BI M13 remains authoritative for semantic consumption.

All M14 controls are local metadata, static validation or deterministic simulation. No
live enforcement, certification, legal advice or production security assurance is claimed.
