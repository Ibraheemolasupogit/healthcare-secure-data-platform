# Snowflake RBAC model

The foundation separates durable ownership from day-to-day access. Permissions are granted to account roles, never directly to users. Identity-to-role assignment is intentionally outside this repository until an approved identity lifecycle exists.

## Role classes

Ownership roles are `PLATFORM_OWNER`, `RAW_OWNER`, `CURATED_OWNER`, `SERVING_OWNER` and `GOVERNANCE_OWNER`, each prefixed by environment. Database and schema ownership follows the layer; warehouse and monitor ownership belongs to the platform owner. Child ownership roles roll into the platform owner, which rolls into `SYSADMIN`.

Functional roles represent human job functions: data engineer, analytics engineer, data-quality analyst, clinical analyst, finance analyst, data scientist, researcher, BI consumer and auditor. Service roles isolate ingestion, transformation and reporting automation. Functional and service roles roll into `SYSADMIN` for administrative visibility, but do not inherit ownership roles.

## Grant rules

- Warehouse `USAGE` is limited to the role's workload.
- Database and schema `USAGE` follows explicit schema allowlists.
- Create privileges exist only for engineering/transformation roles in their designated layers.
- Future `SELECT` applies only to explicitly approved table/view schema pairs.
- Researchers can use only the research warehouse and future approved research products.
- BI consumers and reporting automation can use only the BI warehouse and serving BI schema.
- Auditors receive read-oriented governance access and no business-object creation rights.

The authoritative positive and negative expectations live in `snowflake/config/foundation.json`. Static validation checks referential integrity and the absence of direct-user grants. Connected probes under `snowflake/validation` must later prove actual allow and deny behaviour.

## Administrative separation

The deployment uses separate `ACCOUNTADMIN`, `SECURITYADMIN` and `SYSADMIN` provider aliases because Snowflake management privileges cross these system-role boundaries. This is bootstrap infrastructure authority, not an invitation to use `ACCOUNTADMIN` for normal operation. Connected CI must use protected credentials and limit administrative role assignment to the deployment identity.

## Deferred controls

The `SENSITIVITY_CLASS` tag defines permitted classification values, but no masking or row-access policy is attached in Milestone 3. Consent filtering, pseudonymisation, research expiry/revocation and identity provisioning remain later controlled work. A declared role is not evidence that an identity has been safely assigned to it.
