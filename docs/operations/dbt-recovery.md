# dbt recovery

dbt recovery uses immutable Git commits, manifest checksums, target environment selection,
rebuild order, contract validation and state comparison.

Recovery must not duplicate dbt business logic or run connected builds without approved
credentials and deployment controls.

