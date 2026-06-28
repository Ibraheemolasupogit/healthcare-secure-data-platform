# Core key strategy

Milestone 6 uses `generate_healthcare_surrogate_key()` for stable conformed keys.

Properties:

- SHA-256 based
- null-safe
- derived from canonical business identifiers
- stable across reruns
- independent of row order
- implemented in-project; no package dependency added

Examples:

- `patient_key` derives from `canonical_patient_id`.
- `encounter_key` derives from `canonical_encounter_id`.
- activity keys derive from their source canonical event IDs.

The keys are synthetic portfolio identifiers, not externally meaningful identifiers.
