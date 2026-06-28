# Reconciliation control model

`reconciliation_control_result` is the curated Milestone 9 control output. Its grain is one control date, source system, entity type, currency and control rule.

The model combines Milestone 8 `finance_daily_control` rows with generated domain count controls over governed M8 facts. It then applies deterministic tolerance rules from `assurance_tolerance_rules`.

Key fields:

- `reconciliation_control_key` — SHA-256 deterministic control key.
- `control_rule_id` — finance or generated domain control identifier.
- `source_record_count`, `governed_record_count`, `record_count_variance`.
- `source_amount`, `governed_amount`, `amount_variance`, `tolerance_amount`.
- `reconciliation_status` — `PASS`, `WARNING` or `FAIL`.
- `evidence_reference` — stable local evidence identifier.

The control model does not recalculate tariffs, contract terms, allocations, revenue recognition or balances.
