# ADR 0021: Protected CI/CD and deployment-control ownership

## Status

Accepted, 2026-06-28.

## Context

The platform has local implementations through governance controls, but live infrastructure
delivery needs protected promotion, artefact integrity, policy gates and deployment
evidence. Terraform already owns infrastructure definition and GitHub Actions already owns
repository CI.

## Decision

GitHub Actions coordinates credential-free CI, Terraform validation, non-deploying plan
contracts, policy gates, release metadata and deployment evidence. Terraform remains the
authoritative infrastructure delivery mechanism. Promotion is DEV to TEST to PROD,
plan-before-apply, approval-gated and evidence-producing. Automatic production deployment
and automatic rollback are prohibited.

## Consequences

CI/CD controls are testable locally without cloud credentials. Apply remains disabled until
authorised credentials, protected environments, approvals and evidence capture exist.

## Alternatives considered

- Shell-script deployment outside Terraform: rejected because it would duplicate
  infrastructure ownership.
- Automatic production apply on merge: rejected because it bypasses review and separation
  of duties.
- Deferring all CI/CD design: rejected because later deployment claims need evidence-ready
  controls now.

## Validation

Validation is provided by deployment registry checks, workflow guardrail tests, policy-gate
evaluation, drift simulation and deterministic evidence checksums.

