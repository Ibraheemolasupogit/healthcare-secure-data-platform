# dbt billing development

Local development remains credential-free:

```bash
cd dbt
dbt deps
dbt parse --profiles-dir . --no-partial-parse
cd ..
PYTHONPATH=src pytest tests/unit/test_dbt_milestone8.py
```

The standard profile is parse-only. Do not run connected Snowflake commands without an authorised profile and explicit approval.

