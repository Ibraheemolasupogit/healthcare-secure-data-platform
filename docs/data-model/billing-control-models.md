# Billing control models

Milestone 8 exposes deterministic control differences without implementing Milestone 9 workflows.

Models:

- `billing_exception`: combines source exceptions with transformation-detected invoice and balance variances.
- `finance_daily_control`: compares source daily controls with governed invoice, line, payment, refund and adjustment outputs.

These controls are calculation outputs only. Assignment, prioritisation, remediation status and evidence packs belong to Milestone 9.

