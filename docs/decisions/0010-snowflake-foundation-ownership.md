# ADR 0010: Terraform ownership of the Snowflake foundation

- **Status:** Accepted
- **Date:** 2026-06-23

## Context

The repository contained both numbered Snowflake SQL scaffolds and a Terraform module. Allowing both to create the same durable objects would create competing sources of truth, drift and ambiguous rollback. Local contributors also need meaningful validation without Snowflake credentials.

## Decision

Terraform owns durable Milestone 3 objects: databases, schemas, warehouses, resource monitors, account roles, hierarchy, grants, ownership transfers and tags. All environment roots consume one versioned JSON foundation contract. Python validates that contract and generates deterministic inventory/review artifacts. SQL is limited to connected inspection, RBAC probes and evidence capture. dbt will own future business relations and transformation semantics.

DEV, TEST and PROD have separate roots and state boundaries. Provider aliases use `ACCOUNTADMIN` only where resource-monitor management requires it, `SECURITYADMIN` for roles/grants/ownership and `SYSADMIN` for databases/schemas/tags. Credentials remain external to configuration and connected applies require protected approval.

## Consequences

The contract, Terraform state and generated inventory have clear roles; SQL cannot silently diverge into a second deployment system. Provider administrative boundaries are visible and testable. Changes to the contract affect all environments and therefore require deliberate review and staged promotion. A protected Snowflake account is still required to prove plan/apply and real RBAC behaviour.

## Alternatives considered

Imperative SQL deployment was rejected because lifecycle and drift would be difficult to reconcile across environments. Duplicating configuration in each Terraform root was rejected because environment topology could diverge. Terraform-managing users was deferred because identity lifecycle, authentication and secret handling are outside Milestone 3.

## Validation

Static checks validate naming, references, role cycles, grants, safe SQL and deterministic inventory. Terraform format/init/validate runs for all three roots. An approved live run must later compare Snowflake inventory and RBAC probes with the contract before deployment can be claimed.
