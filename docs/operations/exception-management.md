# Exception management runbook

Milestone 9 exception handling is seed-driven and local-first.

1. Review `reconciliation_exception` for the consolidated exception inventory.
2. Use `high_priority_exception_inventory` for P1/P2 operational focus.
3. Use `exception_remediation_status` for owner, target date, overdue and action fields.
4. Use `exception_lifecycle_event` for deterministic audit-style event history.

Ownership defaults live in `dbt/seeds/assurance/assurance_exception_ownership.csv`.

Future workflow tools may consume these models, but they must not own the finance calculations or bypass the dbt assurance layer.
