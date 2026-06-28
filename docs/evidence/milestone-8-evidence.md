# Milestone 8 evidence

Milestone 8 adds the governed healthcare billing and finance dbt domain.

## Implemented inventory

- 18 billing/finance source relations declared.
- 18 source-aligned staging models.
- 14 intermediate billing/finance calculation models.
- 5 conformed billing dimensions.
- 12 billing/finance facts and one allocation bridge.
- 2 control models.
- Billing/finance macros for decimal casting, signed adjustments, outstanding balance, ageing, variance and currency compatibility.
- Static guardrail tests in `tests/unit/test_dbt_milestone8.py`.

## Calculation ownership

- Tariff matching: `int_billing__selected_tariff`.
- Contract matching: `int_billing__selected_contract`.
- Payment allocation: `int_finance__payment_allocations`.
- Outstanding balance: `int_finance__governed_outstanding_balance`.
- Revenue-event classification: `int_finance__revenue_event_classification`.
- Daily control comparison: `int_finance__daily_control_comparison`.

## Connected execution status

No live Snowflake execution was performed. Contracts are declared and parseable but not runtime-proven.

## Validation performed

```bash
cd dbt && dbt deps
cd dbt && dbt parse --profiles-dir . --no-partial-parse
PATH="$PWD/.venv/bin:$PATH" PYTHONPATH=src make validate
docker compose config
```

Results:

- `dbt deps`: passed; no packages declared.
- `dbt parse`: passed.
- Parsed graph after Milestone 8: 95 models, 563 data tests, 41 sources and 487 macros.
- Full `make validate`: passed.
- Full pytest: 76 passed with 91% coverage.
- Milestone 8 static guardrails: 7 passed.
- Yamllint: passed.
- Snowflake SQLFluff target: passed.
- Snowflake static validation: passed with 174 declared objects.
- Docker Compose config: passed.
- Markdown local link audit: passed.
- `dbt compile`, `dbt source freshness --select source:raw_billing source:raw_finance` and `dbt docs generate`: attempted locally and failed at Snowflake connection with the placeholder profile; this is expected without credentials.
- Terraform, gitleaks and markdownlint executables were not installed locally in this shell.

## Milestone 9 hand-off

Milestone 9 should add cross-system reconciliation orchestration, exception lifecycle, prioritisation, ownership, remediation status and evidence packs over the M8 control outputs.
