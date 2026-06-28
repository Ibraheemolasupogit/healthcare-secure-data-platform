# Power BI deployment-pipeline blueprint

The deployment pipeline blueprint has development, test and production stages.

Promotion requires static metadata validation, source-boundary checks, semantic model
validation, report accessibility metadata, RLS/OLS resolution, refresh-policy validation,
security review, data-owner approval, measure-owner approval and release evidence.

Connection rebinding is environment-specific. Credentials, tenant IDs, real workspace IDs
and real user identities are prohibited in the repository.

No live deployment pipeline is created in Milestone 13.
