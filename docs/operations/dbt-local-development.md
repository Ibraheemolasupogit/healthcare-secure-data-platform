# dbt local development

The local dbt path is credential-free by default.

```bash
cd dbt
dbt parse --profiles-dir . --no-partial-parse
```

The checked-in profile uses placeholder Snowflake credentials only to validate project structure. It must not be used for live execution.

Additional local guardrails run through Python tests:

```bash
pytest tests/unit/test_dbt_milestone5.py
```

Local validation confirms one dbt project, declared sources, source metadata, staging naming, no joins across domains, no conformed models, and no billing/mart work. It does not prove physical Snowflake object existence.
