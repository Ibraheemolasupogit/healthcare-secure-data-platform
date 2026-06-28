# Assurance priority model

`int_assurance__exception_priority` assigns a deterministic priority score and band.

Inputs:

- controlled severity from `assurance_severity_rules`;
- financial value at risk;
- exception age;
- overdue status.

Outputs:

- `priority_score`;
- `priority_band` (`P1` to `P4`);
- `priority_reason`;
- `priority_contributing_factors`.

The model is intentionally transparent rather than predictive. It is not an ML model and does not begin the feature-store milestone.
