# Milestone 5 evidence

Milestone 5 adds dbt sources, freshness metadata, source-aligned staging, tests, documentation, and local guardrails. It does not deploy or execute Snowflake models.

## Implemented inventory

- One dbt project remains under `dbt/`.
- 23 source relations declared across seven source groups.
- 23 staging views created under `dbt/models/staging`.
- 281 dbt data-test nodes parsed from source and staging YAML.
- Five generic dbt tests added: checksum format, synthetic identifier pattern, timestamp ordering, quarantine error presence, and compound uniqueness.
- Four staging utility macro files added: empty-string normalisation, code normalisation, safe casts, and deterministic deduplication.
- Staging contracts documented with `enforced: false` until live Snowflake column types are proven.

## Validation performed

```bash
cd dbt && PATH="../.venv/bin:$PATH" dbt parse --profiles-dir . --no-partial-parse
PATH="$PWD/.venv/bin:$PATH" PYTHONPATH=src pytest tests/unit/test_dbt_milestone5.py -q
PATH="$PWD/.venv/bin:$PATH" PYTHONPATH=src make validate
```

Results:

- dbt parse: passed.
- Milestone 5 static tests: 7 passed.
- Full credential-free `make validate`: passed; gitleaks was not installed locally and remains covered by CI.
- dbt compile, docs generation and source freshness: attempted locally and failed at Snowflake connection with the placeholder profile; this is expected without credentials.

## Live Snowflake status

No live Snowflake execution was performed. Raw interoperability contracts remain static/not deployed unless an authorised Snowflake environment is configured later.

## Deferred

Milestone 6 should implement conformed healthcare core models over this staging layer. It should not include marts, billing, finance, Dataiku, Fabric, feature-store, or Airflow work.
