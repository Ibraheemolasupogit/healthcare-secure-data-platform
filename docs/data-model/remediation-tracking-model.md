# Remediation tracking model

`exception_remediation_status` provides current remediation state for each assurance exception.

Tracked fields include owner, root cause, target resolution date, overdue flag, residual value at risk, lifecycle age band and resolution status.

The current implementation is deterministic and synthetic:

- ownership comes from `assurance_exception_ownership`;
- target dates come from owner defaults;
- remediation actions are rule-based descriptions;
- resolved timestamps and resolution codes are reserved for future authorised workflows.

No external ticket, messaging, orchestration or case-management system is called.
