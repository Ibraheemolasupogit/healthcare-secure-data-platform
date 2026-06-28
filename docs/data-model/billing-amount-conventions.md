# Billing amount conventions

Milestone 7 uses source-system financial conventions only.

- Amounts are generated with Python `Decimal` and quantised to two decimals.
- Stored CSV/JSONL values are strings such as `550.00` to avoid binary floating-point drift.
- `invoice_lines.net_amount = quantity × unit_price`.
- `invoice_lines.gross_amount = net_amount + tax_amount`.
- `invoices.subtotal_amount`, `tax_amount` and `total_amount` equal their invoice lines.
- `outstanding_balances.outstanding_amount = invoiced_amount - payment_amount + refund_amount - adjustment_amount`.
- Control totals compare source row counts and gross amounts for invoices, invoice lines, payments, refunds and adjustments.

These checks prove source arithmetic consistency. They do not claim compliance with any statutory, IFRS, GAAP or local healthcare reimbursement policy.

