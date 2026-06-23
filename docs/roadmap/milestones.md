# Milestone roadmap

Each milestone ends in one reviewable commit (or a small, explicitly related series) and does not claim completion until its validation and evidence are present.

## Current revised roadmap

The target expanded after Milestone 2 from a 15-milestone secure data-platform portfolio to a 17-milestone Healthcare Enterprise Data Platform. Completed work is not reopened. Billing/finance synthetic sources are a focused Milestone 7 extension immediately before billing transformations: doing this earlier would cannibalise completed M2, while doing it inside dbt work would mix source and transformation ownership.

Every milestone must capture a reproducible command/run, validation artifacts, known limitations and a scoped commit. Existing credential-free gates remain mandatory.

| Milestone | Objective and main deliverables | Validation / evidence gate | Explicit exclusions |
|---|---|---|---|
| **1 — Repository foundation (COMPLETE)** | Standards, architecture, ADRs, package/dbt/Snowflake/Terraform/Docker/CI scaffolds | Credential-free lint/test/parse/format/security evidence | Data/platform deployment |
| **2 — Synthetic healthcare data (COMPLETE WITH DOCUMENTED LIMITATIONS)** | 15 deterministic clinical/operational domains, schemas, profiles, CSV/JSONL/FHIR-inspired fixtures, validation and provenance | 19 tests/93% coverage; 1,090-row sample; deterministic checksums | Large execution, formal FHIR, billing domains |
| **3 — Snowflake foundation (COMPLETE LOCALLY; LIVE DEPLOYMENT PENDING)** | Environment-scoped databases, managed schemas, warehouses, monitors, ownership/functional roles, grants and classification tags using a shared contract and Terraform | 31 tests/91% coverage; 174-object inventory; static controls; Terraform validation; live plan/apply and RBAC probes pending | Source loading and dbt models |
| **4 — FHIR and HL7 ingestion** | Synthetic messages, named validation rules/profiles, identifier/terminology mapping, immutable RAW payloads and rejected-message quarantine | Valid/invalid/replay fixtures, provenance and quarantine reconciliation | Live clinical interfaces, conformance claims beyond validator evidence |
| **5 — dbt staging layer** | Sources/freshness and source-aligned staging for batch/FHIR/HL7 canonical inputs | `dbt build`, freshness, schema/code mapping tests and lineage | Conformed core and marts |
| **6 — Healthcare core model** | Conformed patient, identity, organisation, provider, location, encounter, admission, appointment, pathway, treatment/procedure and clinical facts/dimensions | Grain/key/identity/history tests, source reconciliation, contracts and docs | Billing/finance logic |
| **7 — Billing and finance synthetic extension** | Versioned services, products, tariffs, contracts, claims, invoices/lines, payment lifecycle, exceptions and control totals in the existing generator | Determinism, keys, lifecycle/amount rules, checksums and bounded committed samples | dbt billing models or real finance data |
| **8 — Billing and finance dbt domain** | Billable activity, effective tariffs, invoice totals, payment allocation, refunds/adjustments, outstanding balance and revenue models | Known-case unit tests, source/control reconciliation, contracts and lineage | Revenue-assurance workflow orchestration |
| **9 — Reconciliation and revenue assurance** | Control totals, exception classifications, operational finance marts, SLOs and evidence | Injected breaks, balanced/unbalanced scenarios, alert ownership and traceable resolution | BI dashboards and ML |
| **10 — Airflow orchestration** | Cross-platform sensors, retries, backfills, failure handling and evidence workflows | Success/retry/backfill/idempotency tests and single-trigger ownership | Reimplementing dbt DAGs or Snowflake Tasks |
| **11 — Dataiku workflows** | Governed collaborative analytics, preparation, ML experiments, operationalisation and monitoring over trusted products | Connection/role boundaries, reproducibility, lineage and blocked export tests | Warehouse transformation duplication |
| **12 — Governed feature store** | Feature registry, entity keys, ownership, versions, freshness and point-in-time-correct offline access | Leakage/point-in-time/freshness/version tests and lineage | Online serving without a proven latency requirement |
| **13 — Fabric and Power BI** | Certified semantic models and clinical, operational, financial and executive reporting | Measure reconciliation, refresh, persona access, lineage and performance | Curated transformation in BI |
| **14 — Governance and security implementation** | Pseudonymisation, masking, row access, consent, retention, audit integrity, research access and separation of duties | Persona allow/deny tests, expiry/revocation, policy combinations and audit evidence | Unsupported anonymisation/compliance claims |
| **15 — Terraform and environment design** | Repeatable Snowflake/platform identity, storage, network, secret integration, monitoring and protected state/promotion | Plan/apply/policy checks, drift, isolation, approvals and rollback | Unreviewed production apply |
| **16 — Multi-region architecture and recovery** | Residency constraints, replication/failover, RTO/RPO, dependency mapping and operational runbooks | Recovery/failover exercises, data-loss/reconnect evidence and return-to-primary test | Claims based on diagrams alone |
| **17 — Portfolio evidence and polish** | Consolidated evidence index, runbooks, CI/CD releases, benchmarks, demos and claim-to-evidence audit | Clean-room reproduction, link/checksum audit and limitation review | Fabricated evidence or real health data |

Dependencies follow the table order except security, observability, CI and evidence, which are incrementally applied to every milestone and consolidated at their explicit implementation milestones. See the [realignment plan](../architecture/repository-realignment-plan.md) and [target-state architecture](../architecture/target-state-architecture.md).

## Historical 15-milestone baseline

The sections below preserve the original roadmap as an audit trail. They are superseded for work after Milestone 2; their useful requirements have been redistributed above rather than silently removed.

## 1 — Repository foundation and architecture

**Status: complete.**

- **Objective:** establish a secure, maintainable engineering baseline.
- **Deliverables:** repository/docs, ADRs, Python CLI, dbt/Snowflake/Terraform/Docker/CI scaffolds.
- **Validation:** credential-free lint, unit, parse, format, structure and secret checks.
- **Evidence:** command logs, tree, CLI output and CI run.
- **Commit boundary:** `chore: establish milestone 1 foundation`.
- **Dependencies:** Python and optional Docker/Terraform tooling.
- **Exclusions:** datasets, cloud deployment, domain transformations and dashboards.

## 2 — Synthetic healthcare data generator

**Status: complete.**

- **Objective:** generate deterministic, explicitly synthetic, relational healthcare fixtures at configurable scale.
- **Deliverables:** domain schemas, seeded generator, small/medium/large profiles, manifest and validation.
- **Validation:** reproducibility, referential integrity, distributions, synthetic-only invariants and small-mode runtime.
- **Evidence:** manifest, sample quality report, tests and benchmark seed/config.
- **Commit boundary:** `feat: add synthetic healthcare data generator`.
- **Dependencies:** Milestone 1 package/config conventions.
- **Exclusions:** Snowflake loading and large benchmark execution.

## 3 — Snowflake foundations and RBAC

**Current status: implemented and validated locally; live deployment evidence pending.**

- **Objective:** provision environment-scoped accounts objects, compute and least-privilege roles.
- **Deliverables:** Terraform/SQL for databases, schemas, warehouses, monitors, roles and grants.
- **Validation:** idempotent plan/apply, object inventory, positive/negative role matrix and auto-suspend checks.
- **Evidence:** redacted plan, grants, monitor settings and role-test results.
- **Commit boundary:** `feat: provision Snowflake platform foundations`.
- **Dependencies:** 1; isolated Snowflake development account.
- **Exclusions:** ingestion, domain models and sensitive-data policies.

## 4 — Batch and semi-structured ingestion

- **Objective:** load replayable CSV/JSON synthetic sources into immutable RAW.
- **Deliverables:** stages, formats, COPY procedures/utilities, load metadata, quarantine and idempotency.
- **Validation:** good/bad file tests, duplicate replay, provenance, malformed input and recovery.
- **Evidence:** load history, quarantine event and row/file reconciliation.
- **Commit boundary:** `feat: implement raw batch ingestion`.
- **Dependencies:** 2–3.
- **Exclusions:** Snowpipe and transformation beyond load validation.

## 5 — dbt sources, staging and intermediate

- **Objective:** establish tested source contracts and reusable source/business logic.
- **Deliverables:** sources/freshness, staging models, identity/encounter/pathway/code intermediate models.
- **Validation:** `dbt build`, freshness, schema/data/unit tests, grain and lineage rules.
- **Evidence:** artifacts, docs graph and injected test failure.
- **Commit boundary:** `feat: add dbt staging and intermediate layers`.
- **Dependencies:** 2–4.
- **Exclusions:** published marts, snapshots and advanced incrementality.

## 6 — Curated models, marts, snapshots and incrementals

- **Objective:** publish governed reusable entities and consumer products with history/change handling.
- **Deliverables:** conformed facts/dimensions, pseudonym-ready patient entity, priority marts, snapshots and incremental models.
- **Validation:** contracts, history, idempotency, late-arriving data, full-refresh equivalence and mart reconciliation.
- **Evidence:** build artifacts, before/after snapshot and incremental metrics.
- **Commit boundary:** `feat: publish curated healthcare marts`.
- **Dependencies:** 5.
- **Exclusions:** native Streams/Tasks and production BI.

## 7 — Quality, contracts, testing and observability

- **Objective:** make trust measurable and failures actionable.
- **Deliverables:** healthcare rules, contracts, quality events, SLIs/SLOs, alerts and dbt artifact ingestion.
- **Validation:** seeded failure scenarios, ownership routing, contract-breaking change and freshness alert.
- **Evidence:** quality dashboard/report, failed/passed runs and incident record.
- **Commit boundary:** `feat: enforce data quality and observability`.
- **Dependencies:** 5–6.
- **Exclusions:** full enterprise monitoring platform and clinical validation.

## 8 — Snowpipe, Streams, Tasks and change processing

- **Objective:** demonstrate event-driven ingestion and Snowflake-local CDC processing.
- **Deliverables:** Snowpipe design/deployment, Streams, Tasks, retry/replay and monitoring.
- **Validation:** arrival-to-load, duplicate delivery, stream consumption, task failure/recovery and exactly-expected changes.
- **Evidence:** pipe/task histories, latency and recovery trace.
- **Commit boundary:** `feat: add Snowflake native change processing`.
- **Dependencies:** 3–7.
- **Exclusions:** cross-platform Airflow orchestration.

## 9 — Security and research governance

- **Objective:** enforce pseudonymisation, masking, row access and governed research use.
- **Deliverables:** token design, identifier isolation, masking/row policies, consent/cohort rules, access workflow and audit tests.
- **Validation:** persona positive/negative tests, revocation/expiry, policy combinations and disclosure review.
- **Evidence:** redacted role-query comparison, policy DDL and access decision trail.
- **Commit boundary:** `feat: enforce healthcare data access policies`.
- **Dependencies:** 3, 6–7.
- **Exclusions:** claims of anonymisation without formal risk assessment.

## 10 — Performance, scaling, concurrency and cost

- **Objective:** quantify platform behaviour across configured volumes and workloads.
- **Deliverables:** benchmark harness, warehouse/concurrency scenarios, query tuning, resource monitor and cost model.
- **Validation:** repeatable cold/warm runs, concurrency, spill/scan analysis, budget thresholds and scale comparison.
- **Evidence:** protocol, query profiles, metering and results with limitations.
- **Commit boundary:** `perf: benchmark Snowflake workloads and cost`.
- **Dependencies:** 2–9.
- **Exclusions:** universal production sizing guarantees.

## 11 — Airflow orchestration

- **Objective:** coordinate a genuine cross-platform end-to-end workflow.
- **Deliverables:** minimal DAG, external dependency sensors, dbt invocation, retry/SLA and runbook.
- **Validation:** success, retry, backfill, idempotency and no duplicate native schedule.
- **Evidence:** DAG graph, task logs and recovery run.
- **Commit boundary:** `feat: orchestrate cross-platform workflow`.
- **Dependencies:** 4–8.
- **Exclusions:** replacing dbt graph execution or Snowflake Tasks.

## 12 — Dataiku governed research workflow

- **Objective:** demonstrate reproducible approved cohort analysis.
- **Deliverables:** documented project/flow, governed connection, recipes, scenario, export control and handover.
- **Validation:** role boundary, reproducibility, cohort reconciliation and blocked unapproved export.
- **Evidence:** sanitised flow export, scenario log and approval mapping.
- **Commit boundary:** `feat: add governed Dataiku research workflow`.
- **Dependencies:** 6, 9.
- **Exclusions:** unrestricted self-service or production clinical research claims.

## 13 — Fabric and Power BI consumption

- **Objective:** expose governed semantic products for operational/executive reporting.
- **Deliverables:** semantic model, measures, refresh design, reports, RLS mapping and dbt exposures.
- **Validation:** source lineage, measure reconciliation, refresh, access personas and performance.
- **Evidence:** model metadata, redacted report captures and test results.
- **Commit boundary:** `feat: add Fabric and Power BI consumption layer`.
- **Dependencies:** 6–7, 9–10.
- **Exclusions:** duplicated warehouse transformations.

## 14 — CI/CD, Slim CI, deployment and release controls

- **Objective:** safely promote code and infrastructure with changed-scope feedback.
- **Deliverables:** state-aware dbt CI, protected integration jobs, Terraform plan/apply, release/versioning and rollback controls.
- **Validation:** changed-model selection, injected failure, approvals, environment isolation and rollback rehearsal.
- **Evidence:** CI logs, artifacts, release record and protection settings.
- **Commit boundary:** `ci: implement protected platform delivery`.
- **Dependencies:** all deployable capabilities from 3–13.
- **Exclusions:** bypassable production credentials or automatic unreviewed apply.

## 15 — Evidence, runbooks and portfolio polish

- **Objective:** make the system reproducible, supportable and honestly assessable.
- **Deliverables:** architecture pack, evidence index, operating/recovery/security runbooks, demos, limitations and final threat review.
- **Validation:** clean-room walkthrough, recovery exercise, link/checksum audit and claim-to-evidence review.
- **Evidence:** curated redacted evidence bundle and rehearsal record.
- **Commit boundary:** `docs: complete operational evidence portfolio`.
- **Dependencies:** 1–14.
- **Exclusions:** fabricated evidence, unsupported compliance claims and real health data.
