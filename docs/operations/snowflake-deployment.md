# Snowflake deployment runbook

Local validation is the default. Milestone 15 adds a protected plan-before-apply and
deployment-evidence boundary. A connected plan or apply is optional future evidence and
must run only in an isolated Snowflake account with explicit approval.

## Preconditions

1. Review `snowflake/config/foundation.json`, the committed inventory and the RBAC model.
2. Configure an encrypted, locked, versioned remote backend isolated by environment. Do not use local state for a real apply.
3. Create or approve a deployment identity with the required `ACCOUNTADMIN`, `SECURITYADMIN` and `SYSADMIN` role access. Prefer key-pair or workload identity authentication.
4. Supply authentication through Snowflake provider environment variables or an approved profile. Never add secrets to Terraform variables or files.
5. Require protected-environment approval for TEST and PROD. Apply one environment at a time, starting with DEV.
6. Verify the release manifest, plan metadata, plan checksum, commit SHA, environment,
   approval status and service identity before any connected execution.

## Review and apply

```bash
healthcare-platform snowflake-validate
terraform -chdir=infrastructure/terraform/environments/dev init
terraform -chdir=infrastructure/terraform/environments/dev fmt -check
terraform -chdir=infrastructure/terraform/environments/dev validate
terraform -chdir=infrastructure/terraform/environments/dev plan -out=foundation.tfplan
terraform -chdir=infrastructure/terraform/environments/dev show foundation.tfplan
terraform -chdir=infrastructure/terraform/environments/dev apply foundation.tfplan
```

The saved plan and state may contain sensitive account metadata. Store them only in the protected CI/backend boundary and never commit them. Confirm that the plan contains only foundation objects and grants; any user, stage, pipe or business relation is out of scope.

## Post-apply sequence

Run the SQL files listed in `snowflake/deployment/order.json` from 100 through 150 using the indicated evidence role. Capture redacted results, compare live objects with `snowflake/inventory/foundation.json`, and execute positive and negative probes under each test role. Never treat an expected-denial statement as a batch success criterion; run each probe independently and record the Snowflake error.

Do not promote until inventory, hierarchy, grants, warehouse isolation, auto-suspend, monitor assignment and allow/deny behaviour match the contract. Record drift or failed probes as blockers.

## Promotion and rollback

Promote the same reviewed configuration DEV → TEST → PROD with separate state and approval at each boundary. Roll back a faulty code change by correcting configuration and applying a reviewed replacement plan. Destructive teardown is never the default rollback; follow the dedicated teardown runbook only for an explicitly disposable environment.
