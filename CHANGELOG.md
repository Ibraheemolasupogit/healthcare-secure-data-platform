# Changelog

All notable changes will follow Keep a Changelog conventions. The project does not yet publish versioned releases.

## Unreleased

### Added

- Milestone 1 repository, architecture, development, security, and delivery foundations.
- Milestone 2 deterministic synthetic healthcare generator, schemas, profiles, validation,
  provenance, sample datasets, FHIR-inspired examples, CLI commands and tests.
- Milestone 3 credential-free Snowflake foundation contract, Terraform resources for DEV/TEST/PROD,
  deterministic inventory, RBAC expectations, validation SQL, runbooks and static checks.
- Milestone 4 deterministic FHIR-inspired and HL7 v2 ingestion foundation, canonical envelopes,
  identifier crosswalks, quarantine, raw contracts, samples, CLI, tests and evidence.
- Milestone 5 dbt source declarations, freshness metadata, source-aligned staging views,
  staging utility macros, source/staging tests, local guardrails, documentation and evidence.
- Milestone 6 conformed healthcare core dbt models, deterministic synthetic identity reconciliation,
  SHA-256 surrogate keys, core reconciliation outputs, contracts, guardrail tests, documentation and ADR.
- Milestone 7 deterministic billing and finance synthetic source extension with source schemas,
  Decimal-safe lifecycle generation, validation, positive and negative fixtures, CLI helpers,
  static raw contract metadata, documentation and evidence.
- Milestone 8 governed healthcare billing and finance dbt domain with source declarations,
  staging, intermediate calculation paths, dimensions, facts, controls, macros, guardrails,
  documentation, ADR and evidence.
- Milestone 9 healthcare billing reconciliation and revenue assurance controls with tolerance
  seeds, exception ownership, lifecycle, prioritisation, remediation status, revenue-at-risk
  summaries, deterministic evidence packs, guardrails, documentation and ADR.
- Milestone 10 Apache Airflow orchestration foundation with five DAGs, safe CLI/dbt command
  wrappers, typed configuration, bounded sensors, callbacks, local evidence metadata,
  optional Docker profile, guardrails, documentation and ADR.
- Milestone 11 governed Dataiku analytics and MLOps blueprint with trusted-input contracts,
  billing exception prioritisation Flow design, feature specifications, experiment/evaluation
  configuration, approval gates, model card, scenario blueprints, monitoring design, local
  reference execution, guardrails, documentation and ADR.
- Milestone 12 governed offline healthcare feature-store foundation with reusable feature
  registry, entities, feature views, feature sets, dbt feature models, point-in-time local
  retrieval, Dataiku feature-set references, quality rules, evidence, guardrails and ADR.
- Milestone 13 governed Fabric and Power BI consumption layer with workspace blueprints,
  a shared semantic model, central measures and KPIs, RLS/OLS, report specifications,
  refresh/deployment metadata, deterministic reference catalogues, guardrails and ADR.
- Milestone 14 enterprise governance, security, privacy and compliance-control foundation
  with central registry, access simulation, masking/row/object/export/retention/audit
  controls, platform mappings, evidence outputs, guardrails and ADR.
- Milestone 15 protected CI/CD, environment promotion, infrastructure delivery and
  deployment-control foundation with GitHub Actions guardrails, release/deployment
  manifests, policy gates, drift simulation, rollback metadata, evidence outputs and ADR.
- Milestone 16 multi-region resilience and recovery design with symbolic regions,
  residency policies, recovery tiers, dependency graph, failover/failback controls,
  local simulation, recovery evidence outputs, guardrails and ADR.
- Milestone 17 operational observability, incident readiness and recovery-drill
  automation with service health metadata, SLIs, synthetic SLOs, error budgets,
  incident taxonomy, disabled alert-routing blueprints, runbooks, drill scenarios,
  local simulations, evidence outputs, guardrails and ADR.
- Milestone 18 enterprise integration validation and portfolio release-readiness
  with a deterministic golden path, capability and technology matrices, ownership
  matrix, consolidated evidence index, claim validation, local v1.0 release
  manifest, recruiter summary, engineering review guide, demo script and ADR.
