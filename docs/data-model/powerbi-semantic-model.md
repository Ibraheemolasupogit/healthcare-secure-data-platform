# Power BI semantic model

The `healthcare_enterprise` semantic model is a single governed enterprise model with
separated subject areas for healthcare operations, billing and finance, revenue assurance,
and data-science outputs.

The model uses a star-schema consumption pattern with dimensions such as Date, Patient,
Organisation, Provider and Payer, and facts such as Appointments, Encounters, Invoices,
Payments, Outstanding Balances, Reconciliation Controls, Billing Exceptions and
Predictions.

Every table declares grain, primary key, foreign keys, hidden technical columns, visible
business columns, sensitivity, owner, refresh group, storage mode and lineage in
`powerbi/semantic_models/healthcare_enterprise/model.yaml`.

Relationships are explicit, single-direction by default, and avoid many-to-many or
bi-directional filtering. Inactive relationships must declare a reason.
