# Billing entity relationships

The synthetic billing lifecycle is deliberately simple and auditable:

```text
services/products + tariffs + contracts
  -> billable_activity
  -> claims + claim_lines
  -> invoices + invoice_lines
  -> payment_attempts -> payments -> refunds
  -> adjustments
  -> revenue_events + outstanding_balances + daily_control_totals
```

Key source relationships:

- `billable_activity` links to one healthcare source record: encounter or appointment, with optional clinical-event context.
- `claim_lines` and `invoice_lines` link back to `billable_activity`.
- `claims` and `invoices` use synthetic payer and contract references.
- `payments` must reference successful `payment_attempts`.
- `refunds`, `adjustments`, `outstanding_balances` and `revenue_events` remain traceable to invoices.
- `daily_control_totals` summarise invoices, invoice lines, payments, refunds and adjustments for source-control checks.

Relationship validation lives in the synthetic validator. Downstream dbt reconciliation is deferred to Milestones 8 and 9.

