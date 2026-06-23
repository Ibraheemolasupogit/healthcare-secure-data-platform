# Validating generated data

```bash
healthcare-platform validate-data --input-dir data/samples/small
```

Validation reads canonical CSV and checks expected files/columns, required values, date syntax, primary-key uniqueness, code sets and every declared foreign key. It then checks birth/activity ordering, admission/discharge and length of stay, booking order and cancellation reason, pathway completion/wait/breach calculations, specimen/result order and abnormal flags, consent withdrawal/eligibility, cohort consent, and file checksums.

The command writes `validation_report.json` and `.md`, returns zero on success, and returns non-zero on integrity failure. The manifest is required because it supplies the deterministic reference date. Validation is engineering evidence for synthetic fixtures, not clinical validation or regulatory assurance.
