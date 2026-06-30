# Protected CI/CD and promotion architecture

Milestone 15 uses GitHub Actions as the repository CI/CD coordinator and Terraform as the
authoritative infrastructure delivery mechanism. CI validates repository state, produces
local deterministic evidence, and coordinates promotion gates. It does not own dbt
business logic, Airflow orchestration logic, Dataiku scenario logic, feature definitions,
Power BI measures, governance policy semantics or Snowflake infrastructure design.

Promotion model:

```text
validated commit -> DEV plan -> DEV approval -> TEST plan -> TEST approval -> PROD plan -> PROD approval
```

Apply is disabled for this milestone. Future apply jobs must verify the exact commit,
environment, plan checksum, plan age, approval and service identity before execution.

