# Milestone roadmap

Each milestone ends in one reviewable commit (or a small, explicitly related series) and does not claim completion until its validation and evidence are present.

## 1 — Repository foundation and architecture

- **Objective:** establish a secure, maintainable engineering baseline.
- **Deliverables:** repository/docs, ADRs, Python CLI, dbt/Snowflake/Terraform/Docker/CI scaffolds.
- **Validation:** credential-free lint, unit, parse, format, structure and secret checks.
- **Evidence:** command logs, tree, CLI output and CI run.
- **Commit boundary:** `chore: establish milestone 1 foundation`.
- **Dependencies:** Python and optional Docker/Terraform tooling.
- **Exclusions:** datasets, cloud deployment, domain transformations and dashboards.

## 2 — Synthetic healthcare data generator

- **Objective:** generate deterministic, explicitly synthetic, relational healthcare fixtures at configurable scale.
- **Deliverables:** domain schemas, seeded generator, small/medium/large profiles, manifest and validation.
- **Validation:** reproducibility, referential integrity, distributions, synthetic-only invariants and small-mode runtime.
- **Evidence:** manifest, sample quality report, tests and benchmark seed/config.
- **Commit boundary:** `feat: add synthetic healthcare data generator`.
- **Dependencies:** Milestone 1 package/config conventions.
- **Exclusions:** Snowflake loading and large benchmark execution.

## 3 — Snowflake foundations and RBAC

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
