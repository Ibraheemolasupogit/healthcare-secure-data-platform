# Patient identity model

`core_patient_identity` owns deterministic synthetic patient identity for Milestone 6.

Grain: one source patient identifier per namespace and canonical synthetic patient.

Inputs:

- `stg_clinical__patients`
- `stg_interoperability__identifier_crosswalks`
- `stg_interoperability__ingestion_envelopes`

The model uses Milestone 2 patient IDs as canonical truth. Milestone 4 crosswalks and envelopes add source-format identifier evidence. If an identifier cannot resolve or maps to conflicting canonical patients, the exception is surfaced through `core_reconciliation_exceptions`.

This is not probabilistic matching and is not a production Master Patient Index.
