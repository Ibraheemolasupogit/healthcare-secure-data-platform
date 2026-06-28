# Healthcare billing source boundary

Milestone 7 stops at deterministic billing and finance source data.

## In boundary

- Source-like billing reference data, activity, claims, invoices, payment lifecycle events, refunds, adjustments, exceptions, balances and control totals.
- Local validation for source consistency, decimal-safe amount identities, lifecycle chronology and separated negative fixtures.
- Static Snowflake raw contract metadata for future landing-zone review.

## Out of boundary

- dbt billing source declarations, staging views, intermediate allocation logic, curated facts/dimensions, marts and semantic models.
- Revenue recognition, reimbursement policy, payment-allocation policy and finance close logic.
- Airflow, Dataiku, feature store, Fabric, Power BI and live Snowflake loading.

The next implementation milestone should transform these source records in dbt without changing the generator boundary.

