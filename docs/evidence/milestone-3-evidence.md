# Milestone 3 evidence

## Scope and status

Milestone 3 implements a credential-free, environment-scoped Snowflake foundation for DEV, TEST and PROD. It is **declared and locally validated, not deployed**. No Snowflake credentials were used, no provider plan was produced against an account and no live RBAC probe was executed.

## Declared inventory

- Source contract: `snowflake/config/foundation.json`
- Generated inventory: `snowflake/inventory/foundation.json`
- Environments: DEV, TEST and PROD
- Per environment: four databases, 29 schemas, six warehouses, one resource monitor, 17 roles and one tag
- Total: 174 declared objects
- Provider: Snowflake 2.17.0; Terraform: 1.8.5

The inventory is deterministic and embeds the configuration SHA-256 digest. Static validation rejects a stale inventory, duplicate objects, invalid references, cyclic roles, destructive SQL, unresolved tokens and direct user grants.

## Reproduction record

```bash
healthcare-platform snowflake-validate
healthcare-platform snowflake-inventory --output /tmp/hedp-foundation.json
healthcare-platform snowflake-render --environment DEV --output-dir /tmp/hedp-m3-a
healthcare-platform snowflake-render --environment DEV --output-dir /tmp/hedp-m3-b
diff -r /tmp/hedp-m3-a /tmp/hedp-m3-b
terraform fmt -check -recursive infrastructure/terraform
```

Terraform roots for all three environments were initialised without a backend and validated against the pinned provider schema. Local provider installation used release binaries whose SHA-256 digests matched the provider's published checksum file because registry access was unavailable in the execution environment; the committed lock files include Darwin ARM64 and Linux AMD64 hashes.

## Quality evidence

- Python tests: 31 passed with 91% total coverage.
- Python quality: Ruff formatting/lint and strict mypy passed.
- Snowflake contract: static validation passed for 174 declared objects.
- Rendering: repeated DEV previews were byte-identical.
- Terraform: recursive format check and DEV/TEST/PROD validate passed.
- SQL/YAML/dbt/docs/security regression gates: see the final local validation record for this milestone.

## Deferred live evidence

A protected connected run must still provide a reviewed plan/apply, live object inventory, grants and hierarchy, warehouse/monitor settings, positive role probes and independently recorded expected-denial probes. The SQL under `snowflake/validation` and the deployment/validation runbooks define that path. Until then, this repository makes no claim that the objects exist in Snowflake or that RBAC is enforced there.

## Explicit exclusions

No source load, business table/view, dbt model, masking or row-access policy, user assignment, network policy, Stream, Task, share, performance benchmark or teardown was performed.
