# Feature entities

Milestone 12 registers five entities:

- `patient` using `patient_key`;
- `appointment` using `appointment_key`;
- `payer` using `payer_key`;
- `billing_exception` using `reconciliation_exception_key`;
- `source_system` using `source_system`.

These keys are reused from governed upstream models. The feature store does not create alternative canonical identifiers.
