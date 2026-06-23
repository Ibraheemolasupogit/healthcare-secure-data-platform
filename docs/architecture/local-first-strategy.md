# Local-first strategy

Local development covers Python generation/validation, unit tests, dbt parsing and SQL compilation where possible, SQL/YAML/Markdown linting, Terraform formatting/validation, documentation and small synthetic fixtures. Docker supplies a reproducible toolchain.

Production parity is achieved through shared source, model, test, policy and Terraform definitions—not by pretending a local database reproduces Snowflake semantics. Pull requests run credential-free static gates. A later protected integration job will use short-lived authentication and a per-PR Snowflake clone/schema to run `dbt build`, policy tests and deployment checks.

Snowflake is required to validate warehouse isolation, RBAC/grants, masking and row policies, Streams/Tasks, Snowpipe, Time Travel, cloning, query plans, concurrency, resource monitors and cost. Dataiku, Fabric, Power BI and managed Airflow also require external services.

Configuration uses environment variables and example files; credentials belong in a secret manager or workload identity. Local defaults are small and synthetic. Medium and large modes will be opt-in and output paths remain gitignored.

This model avoids lock-in by keeping generation, contracts, transformation intent, documentation and CI portable. Snowflake-specific SQL stays in an explicit adapter/platform boundary and is accepted where native controls are the reason for the platform choice.
