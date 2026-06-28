# Milestone 6 evidence

Milestone 6 adds the conformed healthcare core model above Milestone 5 staging.

## Implemented inventory

- 2 identity intermediate models.
- 3 reconciliation intermediate models.
- 14 curated/core entity models.
- 2 curated/core reconciliation models.
- 4 core macros.
- 1 ADR for core identity, keys and reconciliation.
- 8 static Milestone 6 Python guardrail tests.
- 44 total dbt models parsed after M6, including M5 staging and M6 core/intermediate models.
- 362 dbt data-test nodes parsed after M6.

## Validation performed

```bash
cd dbt && PATH="../.venv/bin:$PATH" dbt parse --profiles-dir . --no-partial-parse
PATH="$PWD/.venv/bin:$PATH" PYTHONPATH=src pytest tests/unit/test_dbt_milestone6.py -q
PATH="$PWD/.venv/bin:$PATH" PYTHONPATH=src make validate
```

Results:

- dbt parse: passed.
- Milestone 6 static tests: 8 passed.
- Full credential-free `make validate`: passed.
- Full pytest: 65 passed with 91% coverage.
- Snowflake static validation: passed with 174 declared objects.
- Docker Compose config: passed.
- Markdown local link check: passed.
- dbt compile, docs generation and source freshness: attempted locally and failed at Snowflake
  connection with the placeholder profile; this is expected without credentials.
- Terraform, markdownlint and gitleaks executables were not installed locally in this shell.

Broader validation is recorded in the final implementation response for this milestone.

## Live Snowflake status

No live Snowflake execution was performed. Core contracts are declared and parseable but not runtime-proven.

## Deferred

Milestone 7 should extend the synthetic generator with billing and finance source contracts only. It should not build dbt billing models, marts, Airflow, Dataiku, Fabric, Power BI or feature-store artefacts.
