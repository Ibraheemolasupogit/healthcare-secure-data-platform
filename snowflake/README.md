# Snowflake foundation

Milestone 14 maps central governance policies to existing Snowflake roles, tags, grants,
masking-policy previews, row-access-policy previews and audit schemas. These mappings are
static contracts only; Terraform and the Snowflake foundation remain authoritative for
durable deployment.

Milestone 3 defines a secure, environment-scoped Snowflake foundation without requiring credentials for local review. `config/foundation.json` is the authoritative contract. Terraform consumes it directly; the Python CLI validates it and generates the committed object inventory.

For each of DEV, TEST and PROD the contract declares four databases, 29 managed-access schemas, six workload-isolated warehouses, one resource monitor, 17 account roles and one classification tag. Names use `HEDP_<ENV>_<OBJECT>`. The complete inventory contains 174 objects.

## Ownership boundary

- Terraform owns databases, schemas, warehouses, resource monitors, roles, grants, ownership transfers and tags.
- SQL under `account`, `databases`, `schemas`, `warehouses`, `monitoring` and `roles` inspects or validates Terraform-managed state.
- SQL under `validation` captures live inventory, hierarchy, grants, monitoring and allow/deny evidence after an approved apply.
- dbt will own future business tables, views, models, tests and contracts. Milestone 3 creates none.
- Future security, ingestion, Streams/Tasks and sharing files remain bounded placeholders for later milestones.

## Credential-free checks

```bash
healthcare-platform snowflake-validate
healthcare-platform snowflake-inventory --output /tmp/hedp-foundation.json
healthcare-platform snowflake-render --environment DEV \
  --output-dir /tmp/hedp-snowflake-preview
terraform -chdir=../infrastructure/terraform/environments/dev init -backend=false
terraform -chdir=../infrastructure/terraform/environments/dev validate
```

The render command creates deterministic preview SQL and RBAC expectations. It does not connect or apply. The inventory records declared—not deployed—state. See the [deployment](../docs/operations/snowflake-deployment.md), [validation](../docs/operations/snowflake-validation.md) and [teardown](../docs/operations/snowflake-teardown.md) runbooks.

Milestone 4 adds static interoperability load contracts under `contracts/` and an explicitly non-deployed DDL preview at `ingestion/062_interoperability_contract_preview.sql`. They reuse existing RAW and GOVERNANCE schemas and do not alter Terraform container ownership.
