# dbt core validation

Credential-free validation:

```bash
make validate
pytest tests/unit/test_dbt_milestone6.py
```

Optional connected Snowflake validation:

```bash
cd dbt
dbt debug --profiles-dir /secure/profile/path --target dev
dbt build --select tag:core --profiles-dir /secure/profile/path --target dev
dbt test --select tag:core --profiles-dir /secure/profile/path --target dev
dbt docs generate --profiles-dir /secure/profile/path --target dev
```

Do not commit credentials, exported patient data or live Snowflake artifacts. Connected execution is not claimed until these commands run successfully in an authorised environment.
