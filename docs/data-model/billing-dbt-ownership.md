# Billing dbt ownership

dbt owns governed billing and finance calculations from Milestone 8 onward. Python remains the source generator and Snowflake remains the future execution platform.

| Area | dbt-owned model path |
|---|---|
| Source declarations | `dbt/models/sources/raw_billing.yml`, `dbt/models/sources/raw_finance.yml` |
| Staging | `dbt/models/staging/billing`, `dbt/models/staging/finance` |
| Tariff matching | `int_billing__tariff_candidates`, `int_billing__selected_tariff` |
| Contract matching | `int_billing__selected_contract` |
| Claim calculations | `int_billing__claim_line_calculations`, `int_billing__claim_totals` |
| Invoice calculations | `int_billing__invoice_line_calculations`, `int_billing__invoice_totals` |
| Payment allocation | `int_finance__payment_allocations` |
| Revenue events | `int_finance__revenue_event_classification` |
| Outstanding balance | `int_finance__governed_outstanding_balance` |
| Controls/exceptions | `billing_exception`, `finance_daily_control` |
| Assurance over governed outputs | `dbt/models/intermediate/assurance`, `dbt/models/curated/assurance` |

Healthcare entity ownership remains with Milestone 6 core models.

Milestone 9 assurance models may classify, prioritise, group and report exceptions over M8 outputs. They must not reimplement M8 tariff, contract, allocation, revenue-event or outstanding-balance calculations.
