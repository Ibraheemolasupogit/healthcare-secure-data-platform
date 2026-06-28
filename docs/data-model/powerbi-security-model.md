# Power BI security model

Milestone 13 defines RLS and OLS blueprints only. No live tenant roles or users are
configured.

RLS roles are role-based and synthetic:

- Enterprise Viewer;
- Healthcare Operations Viewer;
- Billing and Finance Viewer;
- Revenue Assurance Analyst;
- Data Science Consumer.

Object-level security hides sensitive synthetic identifiers, patient-level details,
payment references and assurance evidence references from broad roles. Patient-level
access is not enabled by default.

Sensitivity mappings are documented for Microsoft label alignment, but Microsoft Purview
labels are not applied in this milestone.
