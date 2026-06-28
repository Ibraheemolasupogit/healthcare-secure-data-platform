# Synthetic data model

Milestone 2 implements 15 internally related clinical, operational, research and governance datasets. Milestone 7 extends the same generator with 18 billing and finance source datasets. They resemble operational healthcare concepts but are not derived from real people, authoritative NHS code sets, finance systems, payer extracts or production system exports.

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
| payers | one synthetic payer | Commissioner, insurer, self-pay, charity or sponsor source reference |
| services | one synthetic billable service | Service catalogue reference |
| products | one synthetic product | Product catalogue reference |
| tariffs | one synthetic tariff | Price/effective-date reference |
| contracts | one synthetic contract | Payer-provider commercial source reference |
| billable_activity | one billable source event | Healthcare activity prepared for claims/invoicing |
| claims | one claim header | Source claim lifecycle |
| claim_lines | one claim line | Claim amount and tariff linkage |
| invoices | one invoice header | Source invoice lifecycle |
| invoice_lines | one invoice line | Invoice amount and activity linkage |
| payment_attempts | one collection attempt | Attempt outcome without real card or bank data |
| payments | one posted payment | Synthetic payment receipt |
| refunds | one refund | Synthetic refund event |
| adjustments | one invoice adjustment | Source correction or write-off |
| billing_exceptions | one exception | Billing control exception |
| revenue_events | one source revenue event | Billing/collection event stream |
| outstanding_balances | one invoice balance snapshot | Source ageing and open balance |
| daily_control_totals | one daily control total | Source count and amount reconciliation |

The schema catalogue is generated from typed metadata in `synthetic/schemas/catalog.py`. It records field type, nullability, description, classification, example, primary key, foreign keys and schema version. Patient dates, sex, ethnicity, pseudonyms and postcode sectors would remain sensitive in a real deployment despite being synthetic here.

CSV is canonical for later batch ingestion rehearsal. JSON Lines carries the same records for semi-structured testing. The separate FHIR-inspired bundle is explicitly non-conformant and exists only to exercise later JSON ingestion design. Billing source semantics are documented in [billing source model](billing-source-model.md).
