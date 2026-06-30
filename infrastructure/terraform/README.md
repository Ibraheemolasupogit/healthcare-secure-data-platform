# Terraform foundation

Terraform manages the durable Milestone 3 Snowflake foundation. The reusable `snowflake_foundation` module is called by isolated DEV, TEST and PROD roots, all of which read `snowflake/config/foundation.json`. Snowflake provider 2.17.0 and Terraform 1.8.5 are pinned.

The module creates databases, managed-access schemas, workload warehouses, an environment resource monitor, ownership and functional account roles, role hierarchy, least-privilege grants, ownership transfers and a classification tag. It deliberately creates no users, stages, pipes, business tables, views or dbt models.

## Authentication and administration

Provider configuration contains no credentials. Connected use relies on Snowflake provider environment variables, workload identity or an approved local profile. Three provider aliases express Snowflake's administrative boundaries:

- `ACCOUNTADMIN` manages resource monitors and their warehouse assignment.
- `SECURITYADMIN` manages roles, grants and ownership transfer.
- `SYSADMIN` creates databases, schemas and tags.

These roles are bootstrap authorities, not application personas. Use a protected deployment identity with only the necessary administrative roles; never place credentials in `*.tfvars`, source, state or command history.

## Local validation

```bash
terraform fmt -check -recursive infrastructure/terraform
for environment in dev test prod; do
  terraform -chdir="infrastructure/terraform/environments/${environment}" init -backend=false
  terraform -chdir="infrastructure/terraform/environments/${environment}" validate
done
```

Initialization downloads a provider but validation requires no Snowflake login. A plan or apply is a connected, protected operation and must follow the [deployment runbook](../../docs/operations/snowflake-deployment.md). Each environment requires an encrypted remote backend with locking, versioning, access logging and isolated apply authority before live use.

Milestone 15 adds local release/deployment manifests, plan metadata requirements,
environment-promotion rules, drift simulation and rollback design. It does not run
Terraform apply or provision remote state.

Milestone 16 adds symbolic recovery-region contracts and replication/failover design
metadata only. It does not create secondary Terraform roots, remote state, failover groups
or live regional infrastructure.
## Milestone 17 operations boundary

Operational readiness treats Terraform plan metadata, drift status and rollback
references as local health signals. It does not run `terraform apply`, change
cloud resources, deploy monitoring infrastructure or enable automatic
remediation.
