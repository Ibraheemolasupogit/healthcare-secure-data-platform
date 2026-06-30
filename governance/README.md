# Enterprise governance and security-control registry

Milestone 14 adds one central, repository-managed governance-control foundation for the
synthetic healthcare platform. It reconciles existing Snowflake, dbt, Airflow, Dataiku,
feature-store, Fabric and Power BI metadata into shared policy definitions with
platform-specific mappings.

The registry is local, synthetic, static and simulated. It is not live-enforced, not legal
advice, not independently audited and not a compliance certification.

## Contents

- `registry/` contains controlled domains, classifications, personas, purposes, access,
  masking, row/object, export, retention, audit, service-identity and control metadata.
- `mappings/` maps central controls to Snowflake, dbt, Airflow, Dataiku, feature-store and
  Fabric/Power BI responsibilities.
- `validation/` documents static validation rules.
- `reference/` contains generated deterministic evidence outputs.

Use:

```bash
PYTHONPATH=src python -m healthcare_platform.cli governance validate-registry
PYTHONPATH=src python -m healthcare_platform.cli governance generate-evidence --overwrite
PYTHONPATH=src python -m healthcare_platform.cli governance verify-evidence
```

Milestone 15 deployment controls invoke this registry as a policy gate. Deployment workflows
must call the validator rather than copying governance policy semantics into workflow YAML.

Milestone 16 recovery controls restore governance first and fail closed until policy
checksums, versions and access-control metadata are validated. No live enforcement or
regional policy deployment is claimed.
