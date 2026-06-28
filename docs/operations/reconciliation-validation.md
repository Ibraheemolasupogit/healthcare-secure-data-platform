# Reconciliation validation runbook

Credential-free validation:

```bash
cd dbt
dbt parse --profiles-dir . --no-partial-parse
cd ..
PYTHONPATH=src pytest tests/unit/test_dbt_milestone9.py
```

Connected validation, when authorised Snowflake credentials are available:

```bash
cd dbt
dbt build --select tag:assurance --profiles-dir .
dbt docs generate --profiles-dir .
```

Expected local limitations:

- contracts are declared but not runtime-proven without Snowflake;
- generated evidence is deterministic metadata, not a live warehouse extract;
- no downstream alerting or workflow integration is in scope for Milestone 9.
