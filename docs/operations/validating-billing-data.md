# Validating billing data

Use the shared validator for full source validation:

```bash
healthcare-platform validate-data --input-dir data/samples/small
```

Milestone 7 also provides a billing-named shortcut:

```bash
healthcare-platform validate-billing --input-dir data/samples/small
```

Important billing rules include:

- Decimal-safe line, invoice and balance amount identities.
- Claim, invoice, payment, refund, adjustment and revenue event chronology.
- Successful payments reference successful attempts.
- Failed attempts carry a failure code.
- Control totals match source rows and amounts.

