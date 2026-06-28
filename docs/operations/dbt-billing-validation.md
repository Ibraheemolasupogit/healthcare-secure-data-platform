# dbt billing validation

Credential-free validation:

```bash
ruff format --check src tests
ruff check src tests
mypy src tests
pytest --cov --cov-report=term-missing
yamllint . --no-warnings
sqlfluff lint snowflake --dialect snowflake
cd dbt && dbt deps && dbt parse --profiles-dir . --no-partial-parse
```

Authorised Snowflake execution path:

```bash
dbt debug
dbt source freshness --select source:raw_billing source:raw_finance
dbt build --select tag:billing tag:finance
dbt test --select tag:billing tag:finance
dbt docs generate
```

Document whether each result is declared, parsed, statically validated, compiled, executed or deployed.

