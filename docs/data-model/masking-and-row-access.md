# Masking and row-access controls

Masking policies cover synthetic NHS-number-like identifiers, patient pseudonyms, birth
dates, postcode sectors, payment references, evidence references, model explanation
references and secret metadata.

Row-access policies cover organisation, payer, assurance domain, approved research cohort
and environment scope. The central policy registry owns the policy definition; Snowflake
and Power BI receive platform-specific mappings.
