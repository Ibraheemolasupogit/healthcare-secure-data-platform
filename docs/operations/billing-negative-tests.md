# Billing negative tests

Negative billing fixtures live separately from clean samples:

```bash
healthcare-platform generate-negative --domain billing --profile small \
  --output-dir data/negative_tests/billing --overwrite
healthcare-platform validate-billing --input-dir data/negative_tests/billing
```

The validation command is expected to exit non-zero for this corpus. Injected defects include invoice-line/header amount mismatches, failed payment attempts without failure codes, balance mismatches, invalid chronology and structural null cases.

Do not mix negative fixtures into `data/samples/small`.

