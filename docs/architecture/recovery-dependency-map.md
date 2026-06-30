# Recovery dependency map

The authoritative recovery dependency graph is stored in
`recovery/registry/recovery_controls.yaml`.

Recovery begins with governance registry integrity and deployment controls, then proceeds
through repository, identity/secret prerequisites, Terraform state/contracts, Snowflake,
dbt, governed core products, assurance, orchestration, feature store, Dataiku, Fabric/Power
BI and evidence verification. Consumer layers must not recover before governed data and
policy layers are validated.

