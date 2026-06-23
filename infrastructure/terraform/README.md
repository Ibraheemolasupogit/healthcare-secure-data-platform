# Terraform foundation

Terraform will manage durable Snowflake resources through reusable modules. Root modules live under `environments/<name>` and call narrowly focused modules. Provider and module versions are pinned; plans are reviewed; applies use protected environments and a dedicated least-privilege deployment identity.

State must use an encrypted remote backend with locking, versioning, access logging and environment separation. State may contain sensitive metadata and must never be committed. Credentials are supplied by workload identity or a secret manager, never variables files or provider blocks. Production state and apply authority are isolated from development.

Milestone 1 exposes a no-resource foundation module so `terraform init -backend=false` and `terraform validate` can run without a Snowflake account or provider download. `providers.tf.example` records the future pinned-provider pattern but is intentionally inactive. Milestone 3 will activate it and add resources only after provider-version and ownership semantics are tested.
