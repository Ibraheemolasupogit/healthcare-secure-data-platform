# Power BI local validation

Run local validation with:

```bash
PYTHONPATH=src python -m healthcare_platform.cli powerbi validate-model
PYTHONPATH=src python -m healthcare_platform.cli powerbi generate-reference --overwrite
PYTHONPATH=src python -m healthcare_platform.cli powerbi verify-reference
PYTHONPATH=src pytest tests/unit/test_powerbi_milestone13.py
```

The validation is credential-free and checks semantic tables, governed sources,
relationships, measures, KPIs, RLS, OLS, reports, visuals, refresh groups, deployment
claims, future-scope boundaries and deterministic reference checksums.
