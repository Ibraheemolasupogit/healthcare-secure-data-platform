# Financial sign and rounding conventions

Milestone 8 uses Snowflake `NUMBER(18,2)` arithmetic for governed monetary values.

- Floating-point money arithmetic is prohibited.
- Currency is preserved and compatibility checks are surfaced before arithmetic across records.
- Rounding is explicit to two decimal places for governed line and balance calculations.
- Refund amounts are stored as positive source amounts and added back in the outstanding-balance formula.
- Adjustment source amounts are stored as positive amounts. `DEBIT` and `CORRECTION` are treated as positive signed adjustments; `CREDIT`, `WRITE_OFF` and `CONTRACTUAL` are treated as negative signed adjustments.
- No FX conversion is implemented.

