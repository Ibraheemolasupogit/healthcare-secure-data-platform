# Assurance status model

Milestone 9 uses deterministic status macros in `dbt/macros/assurance/assurance_rules.sql`.

Statuses:

- `PASS` — count and amount variance are within tolerance.
- `WARNING` — a timing difference or open exception requires review.
- `FAIL` — count or amount variance exceeds tolerance.

`daily_assurance_summary`, `month_end_assurance` and `assurance_evidence_pack` use precedence rules so failures outrank warnings and warnings outrank pass status.

The status model is operational assurance metadata. It is not a substitute for a formal finance close or statutory audit.
