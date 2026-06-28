# ADR 0020: Central governance policy registry

Status: Accepted  
Date: 2026-06-28

## Context

The platform has governed data, ML, feature and BI layers. Security and privacy controls
must be consistent across platforms without moving ownership away from Snowflake, dbt,
Airflow, Dataiku, feature store or Power BI.

## Decision

Create one central governance registry with platform-specific mappings. The registry uses
default deny, least privilege, purpose limitation, consent-aware research controls,
separation of duties and qualified compliance language.

Milestone 14 validates metadata and simulates policy decisions locally. It does not deploy
live enforcement and does not claim certification or legal compliance.

## Consequences

- Policy truth is centralised.
- Platforms consume mappings instead of redefining rules independently.
- Compliance mappings are indicative and evidence-linked.
- Future deployment milestones can use these contracts as input for live controls.

## Alternatives considered

- Platform-specific independent rules: rejected due to conflicting policy truth.
- Live policy deployment now: rejected because credentials and organisational approvals
  are intentionally outside this milestone.
- Compliance certification claims: rejected without independent assessment.
