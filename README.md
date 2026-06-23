# Healthcare Secure Data Platform

A production-style, synthetic-only reference platform for learning and demonstrating secure healthcare data engineering. Snowflake is the target data platform and dbt is the transformation, testing, documentation, and lineage centre of gravity.

> **Status — Milestone 1 complete:** this repository currently provides architecture, standards, an installable Python diagnostic CLI, and deployment/CI scaffolding. It does **not** yet ingest, transform, publish, or analyse healthcare records.

## Why this project exists

Healthcare teams need trusted data products without widening access to identifying or sensitive data. The target platform separates ingestion, transformation, governance, research access, reporting, and orchestration so each can evolve without bypassing controls. It is intended for data and analytics engineers, platform and security engineers, data-quality analysts, clinical/operational analysts, approved researchers, and BI consumers.

## Architecture at a glance

Files and JSON land immutably in **RAW**; dbt standardises them in **STAGING**, builds reusable logic in **INTERMEDIATE**, publishes governed entities in **CURATED**, and produces purpose-specific **MART** and **SEMANTIC** interfaces. Snowflake supplies storage, isolated compute, native ingestion/change processing, access controls, sharing, recovery, monitoring, and cost controls. dbt owns SQL transformation logic and its tests, contracts, lineage, and documentation.

Python will generate synthetic data and provide ingestion/validation utilities. Airflow will coordinate cross-platform work only; Snowflake Tasks and dbt remain responsible for their own scheduling domains. Dataiku will support governed research workflows. Fabric and Power BI will consume semantic products rather than recreate transformation logic. Terraform will provision infrastructure, and GitHub Actions will enforce quality and security gates.

Detailed boundaries are documented in [component responsibilities](docs/architecture/component-responsibilities.md) and the [solution overview](docs/architecture/solution-overview.md).

## Local-first development

Developers can install the Python package, lint SQL/YAML/Terraform, and validate structure without a cloud account. Docker pins a small Python/dbt toolchain. Local work validates portable logic; Snowflake-only behaviour—RBAC, policies, Streams, Tasks, Snowpipe, cloning, Time Travel and warehouse economics—must later be tested in an isolated Snowflake development environment. See [local-first strategy](docs/architecture/local-first-strategy.md).

## Planned healthcare domains

Patient demographics and identifiers; encounters, admissions/discharges and outpatient appointments; waiting-list pathways; clinical, pathology and medication events; providers, organisations and locations; research consent and cohorts; audit activity; and data-quality events. No domain dataset has been generated in Milestone 1.

## Data and security principles

The target layers are `RAW → STAGING → INTERMEDIATE → CURATED → MART → SEMANTIC`. RAW is immutable and source-aligned; each later layer progressively standardises, resolves, governs, and serves data.

The design follows least privilege, workload isolation, encryption in transit/at rest, auditable access, data minimisation, and deny-by-default research access. Pseudonymisation replaces direct identifiers but remains reversible under control; anonymisation aims to prevent re-identification; tokenisation uses controlled substitutes; masking changes presentation by role; row policies filter records; encryption protects bytes. These are complementary—not interchangeable—controls.

**Synthetic data only:** real patient data, real NHS numbers, personal data, secrets, connection strings, and production credentials are prohibited from this repository.

## Milestones

- **Implemented now:** Milestone 1 repository foundation and architecture.
- **Planned next:** Milestones 2–7 add the configurable generator, Snowflake foundations, ingestion, dbt layers, and quality/observability.
- **Future extensions:** Milestones 8–15 add native change processing, advanced governance, benchmarking, Airflow, Dataiku, Fabric/Power BI, deployment controls, and evidence/runbooks.

The deliverables and gates for all 15 milestones are in the [milestone roadmap](docs/roadmap/milestones.md).

## Repository map

| Path | Responsibility |
|---|---|
| `src/healthcare_platform` | Python CLI and future generator/utility package |
| `dbt` | Transformation project conventions and future models |
| `snowflake` | Modular, numbered deployment SQL scaffolding |
| `infrastructure` | Terraform modules/environments and Docker tooling |
| `orchestration`, `dataiku`, `fabric` | Deliberately bounded downstream/cross-platform scaffolds |
| `docs` | Architecture, ADRs, governance, security, roadmap, learning and evidence |
| `tests` | Unit/integration test foundations |
| `.github/workflows` | Credential-free Milestone 1 quality gates |

## Quick start (foundation validation)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e .
healthcare-platform info
make validate
```

Docker alternative: `docker compose build && docker compose run --rm dev make validate`.

These commands validate scaffolding only; no Snowflake connection is attempted. Copy `.env.example` to `.env` only for local, non-secret configuration.

## Limitations

There are no generated records, production resources, dbt domain models, live security policies, dashboards, research workflows, benchmarks, or deployment evidence yet. Provider versions and external-service behaviour must be revalidated when those milestones begin. The example SQL is intentionally non-executable design scaffolding until environment variables and deployment ordering are implemented.

## Portfolio positioning

This is an evidence-led engineering portfolio: each later capability must be implemented, tested, measured, and captured before it is claimed. The architecture prioritises practical Snowflake/dbt depth while keeping business rules portable where reasonable. See the [evidence plan](docs/evidence/evidence-plan.md).

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing the project. Report security concerns using [SECURITY.md](SECURITY.md). This repository is licensed under the [MIT License](LICENSE).
