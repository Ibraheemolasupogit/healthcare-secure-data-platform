# Exception lifecycle model

Milestone 9 consolidates failed controls and Milestone 8 billing exceptions into `reconciliation_exception`, then derives lifecycle state in `exception_remediation_status` and lifecycle events in `exception_lifecycle_event`.

Lifecycle status is deterministic and rule-driven:

- lower-severity exceptions remain `OPEN`;
- medium exceptions are `TRIAGED`;
- high and critical exceptions are `ASSIGNED`;
- terminal statuses are reserved for future authorised remediation workflows.

The seed `assurance_lifecycle_transitions` documents allowed lifecycle movements. Milestone 9 records synthetic lifecycle events only; it does not implement Airflow, service desk integration, notification delivery or human workflow state changes.
