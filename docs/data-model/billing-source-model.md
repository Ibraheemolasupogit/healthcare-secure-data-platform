# Billing and finance synthetic source model

Milestone 7 extends the existing deterministic generator with source-aligned billing and finance records. These are raw-source fixtures, not governed accounting facts, revenue-recognition models or marts.

## Scope

The generator now emits these billing datasets:

- Reference: `payers`, `services`, `products`, `tariffs`, `contracts`.
- Activity and claims: `billable_activity`, `claims`, `claim_lines`.
- Invoicing and collection: `invoices`, `invoice_lines`, `payment_attempts`, `payments`, `refunds`, `adjustments`.
- Controls: `billing_exceptions`, `revenue_events`, `outstanding_balances`, `daily_control_totals`.

Billing records link back to synthetic healthcare sources through patient, encounter, appointment, provider, organisation and clinical-event identifiers. Source financial values are held as two-decimal strings generated from Python `Decimal` arithmetic.

## Explicit non-goals

Milestone 7 does not implement dbt billing sources, staging models, facts, dimensions, marts, semantic models, payment allocation, revenue-recognition policy, Airflow, Dataiku, Fabric, Power BI or live Snowflake loading.

