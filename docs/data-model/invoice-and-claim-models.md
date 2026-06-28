# Invoice and claim models

Claim lines and invoice lines preserve source values and calculate governed values from the selected tariff where available.

Published models:

- `fct_claim`
- `fct_claim_line`
- `fct_invoice`
- `fct_invoice_line`

Claim and invoice headers preserve source totals and expose governed totals from governed line calculations. Variance fields show source-to-governed differences. Source header totals are not treated as automatically authoritative.

No payer adjudication, accounting policy or formal revenue recognition is implemented in Milestone 8.

