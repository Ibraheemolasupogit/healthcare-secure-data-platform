# Billing and finance dbt domain

Milestone 8 moves Milestone 7 billing/finance source fixtures into governed dbt models. It declares the source contracts, stages the relations, centralises reusable calculations in intermediate models, and publishes reusable curated billing/finance dimensions, facts and controls.

## Layer ownership

- Sources: `raw_billing` and `raw_finance` declarations for Milestone 7 relations.
- Staging: source-grain `stg_billing__*` and `stg_finance__*` models.
- Intermediate: one tariff-selection path, one contract-selection path, one payment-allocation path, one outstanding-balance path, and shared claim/invoice/revenue/control calculations.
- Curated billing: payer/service/product/tariff/contract dimensions; billable activity, claim, claim-line, invoice and invoice-line facts; billing exception control model.
- Curated finance: payment-attempt, payment, payment-allocation, refund, adjustment, revenue-event and outstanding-balance facts; daily control comparison.

Milestone 8 does not implement operational reconciliation workflows, case assignment, revenue-assurance prioritisation, Airflow, Dataiku, feature-store, Fabric, Power BI or external accounting integrations.

