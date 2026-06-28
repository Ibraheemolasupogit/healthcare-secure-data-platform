# dbt Snowflake execution

Milestone 5 does not run live Snowflake commands. Connected execution is optional and requires explicit credentials and user authorisation.

To run in an approved Snowflake DEV environment, provide a separate profile outside the committed placeholder file. Use short-lived or managed credentials where possible.

Suggested connected sequence:

```bash
cd dbt
dbt debug --profiles-dir /secure/profile/path --target dev
dbt source freshness --profiles-dir /secure/profile/path --target dev
dbt build --select tag:milestone_5 --profiles-dir /secure/profile/path --target dev
dbt docs generate --profiles-dir /secure/profile/path --target dev
```

Connected runs should record the target account, role, warehouse, environment, selected models, elapsed time, failures, and generated artifacts. Do not commit credentials, raw exports, or live patient data.
