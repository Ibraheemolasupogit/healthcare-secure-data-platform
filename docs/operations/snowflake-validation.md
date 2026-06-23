# Snowflake validation runbook

Milestone 3 has two evidence classes: credential-free declaration checks and optional connected Snowflake checks. They must not be conflated.

## Credential-free validation

```bash
healthcare-platform snowflake-validate
healthcare-platform snowflake-inventory --output /tmp/hedp-foundation.json
healthcare-platform snowflake-render --environment DEV --output-dir /tmp/hedp-preview-a
healthcare-platform snowflake-render --environment DEV --output-dir /tmp/hedp-preview-b
diff -r /tmp/hedp-preview-a /tmp/hedp-preview-b
terraform fmt -check -recursive infrastructure/terraform
```

Then initialise and validate each Terraform root. These checks prove contract integrity, deterministic rendering, inventory consistency, valid Terraform/provider schemas, safe SQL patterns and the absence of direct grants to users. They do not prove provider authentication, plan correctness against a specific account or Snowflake enforcement.

## Connected validation

After an approved apply, execute `snowflake/validation/100_object_inventory.sql` through `150_monitoring.sql` in deployment order. Validate:

- expected object names/counts and environment isolation;
- ownership hierarchy and absence of direct user grants;
- exact warehouse usage and schema privileges;
- allowed persona queries;
- denied persona actions, recording each expected error independently;
- warehouse auto-suspend, initial suspension, timeouts and monitor assignment;
- resource-monitor quota and thresholds.

RBAC probes must use test identities or controlled role switching. Redact account locators, usernames, query IDs and sensitive metadata before saving evidence. A query run as an administrative role is not valid persona evidence.

## Failure handling

Do not apply forward to hide a mismatch. Preserve the reviewed plan and redacted output, compare the live object with the JSON contract and Terraform state, and classify the issue as configuration error, drift, provider behaviour or insufficient deployment authority. Correct code or state ownership through a reviewed process, rerun the failed layer and document the limitation.
