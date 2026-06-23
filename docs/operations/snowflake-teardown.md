# Snowflake teardown runbook

Teardown is permitted only for an explicitly disposable environment with named approval. It is not a routine rollback and must never target production merely because an apply failed.

## Preconditions

1. Confirm the Terraform workspace/backend and Snowflake account are the intended disposable environment.
2. Review dependencies, retained evidence and any later-milestone data. Milestone 3 itself creates no business data.
3. Capture a final redacted inventory and approved state backup.
4. Disable dependent jobs and obtain environment-owner approval.
5. Review a destroy plan; reject any object outside the `HEDP_<ENV>_` boundary.

## Controlled destruction

```bash
terraform -chdir=infrastructure/terraform/environments/dev plan -destroy -out=destroy.tfplan
terraform -chdir=infrastructure/terraform/environments/dev show destroy.tfplan
terraform -chdir=infrastructure/terraform/environments/dev apply destroy.tfplan
```

Never use ad hoc SQL to race Terraform deletion. If ownership or grants prevent destruction, investigate state and Snowflake ownership rather than force-removing state entries.

## Verification

Confirm that environment-prefixed databases, warehouses, monitor and roles are absent, no shared object was removed, and the remote state contains no managed resources. Retain only redacted evidence permitted by policy, then revoke the deployment identity's temporary administrative access.

Production teardown requires a separate recovery and retention plan, senior approval and service-owner coordination; this runbook alone is insufficient.
