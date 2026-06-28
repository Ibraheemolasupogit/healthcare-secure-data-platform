# Controlled vocabularies

`synthetic/code_sets.py` defines explicit portfolio code sets for organisation/location type, provider role, specialty, sex, ethnicity, encounter type/status, attendance status, pathway status/stage, consent status, clinical and medication event types, pathology status, audit action, quality severity, payer type, service/product categories, contract type, pricing basis, claim/invoice/payment/refund statuses, payment method, adjustment type, billing exception type, revenue event type, ageing bucket, billing status and currency.

These codes are intentionally small, synthetic and pedagogical. They are not authoritative NHS Data Dictionary, SNOMED CT, dm+d, ICD, OPCS, HL7 or FHIR terminology. Production mapping would require licensing, terminology governance, version/effective dates and clinical review.

Validators reject uncontrolled values for fields linked to a code set. Synthetic diagnosis, pathology, medication and event codes carry a visible `SYN-` prefix.
