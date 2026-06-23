# Synthetic data model

Milestone 2 implements 15 internally related, synthetic-only datasets. They resemble operational healthcare concepts but are not derived from real people, authoritative NHS code sets, or production system extracts.

| Dataset | Grain | Purpose |
|---|---|---|
| organisations | one synthetic organisation | Provider hierarchy |
| locations | one delivery location | Sites, wards, clinics, labs and virtual care |
| providers | one synthetic provider | Workforce relationships without names |
| patients | one synthetic pseudonymised person | Demography and registration |
| encounters | one care contact | Cross-setting activity |
| admissions | one inpatient episode | Admission/discharge and readmission |
| appointments | one outpatient booking | Scheduling and attendance |
| pathways | one waiting-list pathway | Deterministic clock and breach state |
| clinical_events | one clinical event | Observation, diagnosis, procedure or referral |
| pathology_results | one test result | Specimen/result timing and ranges |
| medication_events | one medication lifecycle event | Prescription through review/discontinuation |
| research_consent | one consent decision | Research-use eligibility |
| research_cohorts | one cohort membership | Consent-gated approved membership |
| audit_events | one synthetic platform action | Governance activity |
| data_quality_events | one injected defect | Negative-test traceability |

The schema catalogue is generated from typed metadata in `synthetic/schemas/catalog.py`. It records field type, nullability, description, classification, example, primary key, foreign keys and schema version. Patient dates, sex, ethnicity, pseudonyms and postcode sectors would remain sensitive in a real deployment despite being synthetic here.

CSV is canonical for later batch ingestion rehearsal. JSON Lines carries the same records for semi-structured testing. The separate FHIR-inspired bundle is explicitly non-conformant and exists only to exercise later JSON ingestion design.
