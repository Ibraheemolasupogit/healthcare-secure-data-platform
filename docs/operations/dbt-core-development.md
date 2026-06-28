# dbt core development

Use Milestone 5 staging models as the only entry point into source data.

```bash
cd dbt
dbt parse --profiles-dir . --no-partial-parse
cd ..
pytest tests/unit/test_dbt_milestone6.py
```

Rules:

- curated/core models must not call `source()`;
- core SQL must not implement billing, finance, marts or downstream platform logic;
- new entity definitions must be added once and documented in `core-entity-ownership.md`;
- surrogate keys must use `generate_healthcare_surrogate_key()`;
- unmatched or conflicting records must be surfaced through reconciliation outputs.
