# Feature-store validation

Credential-free validation:

```bash
PYTHONPATH=src python -m healthcare_platform.cli feature-store validate-registry
PYTHONPATH=src pytest tests/unit/test_feature_store_milestone12.py
cd dbt && dbt parse --profiles-dir . --no-partial-parse
```

Connected Snowflake validation should later run `dbt build --select tag:feature_store` with approved credentials.
