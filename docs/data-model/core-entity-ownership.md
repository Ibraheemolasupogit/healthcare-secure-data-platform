# Core entity ownership

| Concept | Authoritative dbt model | Grain |
|---|---|---|
| Patient identity | `core_patient_identity` | one source patient identifier per namespace |
| Patient | `core_patient` | one canonical synthetic patient |
| Organisation | `core_organisation` | one canonical organisation |
| Location | `core_location` | one canonical location |
| Provider | `core_provider` | one canonical provider |
| Encounter | `core_encounter` | one canonical encounter |
| Admission | `core_admission` | one admission |
| Appointment | `core_appointment` | one appointment |
| Pathway | `core_pathway` | one pathway |
| Clinical event | `core_clinical_event` | one clinical event |
| Pathology result | `core_pathology_result` | one pathology result |
| Medication event | `core_medication_event` | one medication event |
| Consent | `core_consent` | one consent record |
| Research eligibility foundation | `core_research_eligibility` | one patient/cohort eligibility row |
| Reconciliation exceptions | `core_reconciliation_exceptions` | one surfaced exception |

Downstream milestones must reuse these models rather than creating parallel patient, encounter, organisation or activity definitions. Milestone 8 billing models link to these core models for healthcare context and preserve unmatched references instead of rebuilding healthcare entities.
