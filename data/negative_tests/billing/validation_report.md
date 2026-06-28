# Synthetic data validation report

- Result: **FAIL**
- Datasets: 33
- Rows: 2145
- Issues: 8

## Issues

- `STRUCT-NULL` `claims` `CLM-000000080` — payer_id is required
- `BR-APT-001` `appointments` `APT-000000001` — cancellation reason does not align with status
- `TIME-TRF-001` `tariffs` `TRF-000000001` — tariff valid_to precedes valid_from
- `TIME-BACT-001` `billable_activity` `BACT-000000123` — activity must follow birth_date
- `FIN-INVL-002` `invoice_lines` `INVL-000000111` — gross does not equal net plus tax
- `FIN-INV-002` `invoices` `INV-000000111` — invoice totals do not equal lines
- `BR-PATM-001` `payment_attempts` `PATM-000000094` — failed attempt lacks failure code
- `FIN-BAL-001` `outstanding_balances` `BAL-000000111` — outstanding balance mismatch
