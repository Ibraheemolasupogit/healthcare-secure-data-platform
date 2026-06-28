# Credential management

The repository contains examples and variable names only. `.env` is gitignored and is not an acceptable production secret store. Human Snowflake access should use SSO/MFA. Automation should prefer workload identity or encrypted key-pair authentication, scoped per environment and service.

GitHub environment secrets will eventually hold references or protected values such as `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PRIVATE_KEY`, `SNOWFLAKE_ROLE`, and `SNOWFLAKE_WAREHOUSE`; integration workflows remain disabled unless the protected environment is explicitly invoked. Never print these values or pass them as command-line arguments.

Secrets require named ownership, least privilege, rotation, expiry where supported, access logging and immediate revocation after exposure. CI scans commits, private keys and dependency configuration. Terraform state is encrypted, access-controlled, locked and treated as sensitive.

Airflow Milestone 10 DAGs do not embed credentials or pass secrets in command strings. Fixture mode is the default. Connected Snowflake mode must use approved dbt/Snowflake credential mechanisms and remains disabled unless explicitly configured.
