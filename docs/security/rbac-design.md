# RBAC design

Snowflake privileges flow from object ownership roles into functional roles; users and service accounts receive functional roles, not direct grants. Proposed functional roles are platform administrator, data engineer, analytics engineer, data-quality analyst, clinical analyst, operational analyst, approved researcher, BI consumer and service account.

Platform administration is separated from security administration and routine object creation. Engineers can build only in their environment. Analysts read approved marts. Researchers receive project-specific child roles with cohort row policies and expiry. BI service roles read semantic products only. Service roles cannot grant privileges.

Future tests will impersonate each role and assert both allowed and denied operations. Ownership transfer, future grants, managed-access schemas and role hierarchy changes require review. Break-glass access is time-bound, logged and retrospectively reviewed.
