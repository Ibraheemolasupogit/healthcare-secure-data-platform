# Milestone 9 evidence

Milestone 9 adds healthcare billing reconciliation, exception management and revenue assurance controls over the Milestone 8 governed billing and finance dbt domain.

## Implemented inventory

- 5 assurance rule seeds.
- 4 assurance macros.
- 5 intermediate assurance models.
- 10 curated assurance models.
- Deterministic evidence-pack CLI: `healthcare-platform assurance-evidence`.
- Static guardrail tests in `tests/unit/test_dbt_milestone9.py`.

## Boundary evidence

- Assurance models do not call `source()`.
- Assurance models reference Milestone 8 outputs such as `finance_daily_control`, `billing_exception`, billing facts and finance facts.
- M8 remains the owner of tariffs, contracts, allocation, revenue events, outstanding balances and finance control calculations.

## Validation to perform

```bash
cd dbt && dbt deps
cd dbt && dbt parse --profiles-dir . --no-partial-parse
PYTHONPATH=src pytest tests/unit/test_dbt_milestone9.py
PYTHONPATH=src python -m healthcare_platform.cli assurance-evidence --output-dir /tmp/m9-assurance-evidence --overwrite
make validate
docker compose config
```

Connected Snowflake validation should later run `dbt build --select tag:assurance` and `dbt docs generate`.

## Known limitations

- Contracts are declared and parseable but not runtime-proven without Snowflake credentials.
- Evidence packs are local metadata artifacts.
- No Airflow, Dataiku, Fabric, Power BI, feature store, notification or external workflow integration is implemented.
