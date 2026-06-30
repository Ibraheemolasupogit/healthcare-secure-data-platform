# Platform ownership map

Each platform layer has one primary owner. Overlays reference component
metadata rather than taking ownership of upstream logic.

- Interoperability owns FHIR/HL7 source contracts.
- Snowflake owns platform storage and security foundations.
- dbt owns shared transformations and governed data products.
- Airflow owns cross-platform orchestration metadata.
- Dataiku owns the analytics/MLOps blueprint.
- Feature store owns reusable offline features.
- Fabric/Power BI owns governed consumption metadata.
- Governance owns policy metadata and access simulation.
- Deployment owns promotion, drift and rollback metadata.
- Recovery owns recovery tiers and failover/failback design.
- Operations owns health, incident and drill simulation.
- Portfolio owns final evidence and reviewer navigation.
