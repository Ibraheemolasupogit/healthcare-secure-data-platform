# Revenue-at-risk model

`revenue_at_risk_summary` groups high-priority assurance exceptions by currency, assigned owner and priority band.

Value at risk comes from the upstream exception record:

- direct amount variances use the absolute reconciliation variance;
- Milestone 8 billing exceptions carry their governed financial value at risk;
- grouped duplicate exceptions are linked by `linked_exception_group_key`;
- only primary exceptions are included in `total_value_at_risk`.

This prevents the same underlying issue from being counted multiple times across related controls.

Milestone 9 does not define formal revenue-recognition policy. It provides operational revenue-assurance indicators over already-governed M8 outputs.
