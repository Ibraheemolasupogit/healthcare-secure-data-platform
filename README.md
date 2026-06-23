# Healthcare Secure Data Platform

A production-style, synthetic-only Healthcare Enterprise Data Platform portfolio for clinical, operational, research and financial data engineering. Snowflake remains the target governed data platform and dbt remains the transformation, testing, documentation, lineage and business-logic centre of gravity.

> **Status — Milestone 4 complete locally:** deterministic FHIR-inspired resources and synthetic HL7 v2.5 messages are generated, parsed, validated, mapped and quarantined without credentials. Snowflake loading and formal standards conformance are not claimed. dbt models and later platform integrations remain planned.

## Why this project exists

Healthcare teams need trusted clinical, operational and financial data products without widening access to identifying or sensitive data. The target platform separates interoperability, ingestion, transformation, governance, billing controls, analytics/ML, research access, reporting and orchestration so each can evolve without bypassing controls. It is intended for data and analytics engineers, platform and security engineers, data-quality and finance-control analysts, clinical/operational analysts, approved researchers, data scientists and BI consumers.

## Architecture at a glance

Files and JSON land immutably in **RAW**; dbt standardises them in **STAGING**, builds reusable logic in **INTERMEDIATE**, publishes governed entities in **CURATED**, and produces purpose-specific **MART** and **SEMANTIC** interfaces. Snowflake supplies storage, isolated compute, native ingestion/change processing, access controls, sharing, recovery, monitoring, and cost controls. dbt owns SQL transformation logic and its tests, contracts, lineage, and documentation.

Python now generates synthetic data and validates its structure and relationships. Future FHIR/HL7 and batch ingestion will validate and map source messages before Snowflake RAW. Airflow will coordinate cross-platform work only; Snowflake Tasks and dbt remain responsible for their own scheduling domains. Dataiku will consume governed products for collaborative analytics and ML. A governed feature store will register reusable, point-in-time-correct features. Fabric and Power BI will consume certified semantic products rather than recreate transformation logic. Terraform will provision infrastructure, and GitHub Actions will enforce quality and security gates.

Detailed boundaries are documented in [component responsibilities](docs/architecture/component-responsibilities.md), the [target-state architecture](docs/architecture/target-state-architecture.md), and the [repository realignment plan](docs/architecture/repository-realignment-plan.md).

## Implementation status by capability

| Capability | Responsibility | Current status |
|---|---|---|
| Python synthetic platform | Deterministic source data, schemas, validation and provenance | **Implemented locally** for M2 domains |
| Interoperability | Synthetic FHIR-inspired/HL7 generation, parsing, envelopes and quarantine | **Implemented locally for the bounded M4 subset** |
| Snowflake | Governed central storage/compute, RAW-to-serving layers and access enforcement | **M3 foundation declared and statically validated; not deployed** |
| dbt | Transformation, testing, documentation, lineage, dimensional models, contracts and business logic | **Parseable skeleton only; planned** |
| FHIR and HL7 | Source interoperability, validation, canonical mapping and quarantine | **FHIR-inspired fixture only; parsers planned** |
| Airflow | Cross-platform orchestration, retries, backfills and failure handling | **Placeholder only; planned** |
| Dataiku | Governed analytics, feature engineering, ML, experiments and model monitoring | **Placeholder only; planned** |
| Feature store | Governed reusable features, ownership, freshness, versions and point-in-time correctness | **Not implemented; planned** |
| Fabric and Power BI | Certified semantic consumption and operational/financial/executive reporting | **Placeholder only; planned** |
| Terraform | Repeatable infrastructure, identity, storage, networking, secrets and monitoring | **Snowflake foundation module implemented; no apply performed** |
| Governance/security | RBAC, masking, pseudonymisation, row access, consent, retention and audit | **M3 roles/grants/tags declared; policies remain planned** |

## Local-first development

Developers can install the Python package, lint SQL/YAML/Terraform, and validate structure without a cloud account. Docker pins a small Python/dbt toolchain. Local work validates portable logic; Snowflake-only behaviour—RBAC, policies, Streams, Tasks, Snowpipe, cloning, Time Travel and warehouse economics—must later be tested in an isolated Snowflake development environment. See [local-first strategy](docs/architecture/local-first-strategy.md).

## Implemented synthetic healthcare domains

The generator covers organisations, locations, providers, patients, encounters, admissions/discharges, outpatient appointments, waiting-list pathways, clinical events, pathology results, medication events, research consent and cohorts, audit activity, and controlled data-quality events. The committed sample uses 100 patients and proportionate related records. See the [synthetic data model](docs/data-model/synthetic-data-model.md).

The expanded target preserves those healthcare concepts and plans explicit treatments/procedures plus services, products, tariffs, contracts, claims, invoices/invoice lines, payment attempts, payments, refunds, adjustments, failed payments, billing exceptions, revenue and outstanding balances. These billing and finance entities are **not** part of the current generator; they are a focused future extension before billing dbt implementation.

## Data and security principles

The target layers are `RAW → STAGING → INTERMEDIATE → CURATED → MART → SEMANTIC`. RAW is immutable and source-aligned; each later layer progressively standardises, resolves, governs, and serves data.

The design follows least privilege, workload isolation, encryption in transit/at rest, auditable access, data minimisation, and deny-by-default research access. Pseudonymisation replaces direct identifiers but remains reversible under control; anonymisation aims to prevent re-identification; tokenisation uses controlled substitutes; masking changes presentation by role; row policies filter records; encryption protects bytes. These are complementary—not interchangeable—controls.

**Synthetic data only:** real patient data, real NHS numbers, personal data, secrets, connection strings, and production credentials are prohibited from this repository.

## Milestones

- **Complete:** Milestone 1 repository foundation.
- **Complete with documented limitations:** Milestone 2 deterministic synthetic healthcare generation.
- **Complete locally; live evidence pending:** Milestone 3 Snowflake foundation.
- **Complete locally:** Milestone 4 FHIR and HL7 ingestion foundation.
- **Recommended next:** Milestone 5 dbt staging layer.
- **Planned:** Milestones 5–17 add dbt healthcare core, billing/finance and reconciliation, Airflow, Dataiku, feature store, Fabric/Power BI, executable governance, broader Terraform, multi-region recovery and portfolio evidence.

The original 15-milestone plan has been transparently realigned into a 17-milestone dependency-led [roadmap](docs/roadmap/milestones.md). [ADR 0009](docs/decisions/0009-expand-to-healthcare-enterprise-platform.md) records why.

## Repository map

| Path | Responsibility |
|---|---|
| `src/healthcare_platform` | Python CLI, generator, schemas, writers and validation |
| `data/samples/interoperability` | Reviewed FHIR-inspired, HL7, envelope, crosswalk and manifest samples |
| `config/synthetic` | Small, medium and large generation profiles |
| `data/samples/small` | Reviewed 100-patient synthetic sample and evidence |
| `dbt` | Transformation project conventions and future models |
| `snowflake` | Foundation contract, inventory and live-validation SQL |
| `infrastructure` | Terraform modules/environments and Docker tooling |
| `orchestration`, `dataiku`, `fabric` | Deliberately bounded downstream/cross-platform scaffolds |
| `docs` | Architecture, ADRs, governance, security, roadmap, learning and evidence |
| `tests` | Unit and integration tests, including determinism and integrity |
| `.github/workflows` | Credential-free quality gates |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e .
healthcare-platform info
healthcare-platform describe-profile small
healthcare-platform generate --profile small --seed 42 \
  --reference-date 2025-01-01 --output-dir data/generated/small
healthcare-platform validate-data --input-dir data/generated/small
make validate
```

Docker alternative: `docker compose build && docker compose run --rm dev make validate`.

Generation uses no network service and makes no Snowflake connection. Existing output is not overwritten unless `--overwrite` is supplied. The committed sample at `data/samples/small` contains canonical CSV, equivalent JSON Lines, lightweight FHIR-inspired resources, a schema catalogue, manifest, checksums and validation reports. Those FHIR-inspired resources are not formally conformant.

The Snowflake foundation can be checked without credentials:

```bash
healthcare-platform snowflake-validate
healthcare-platform snowflake-render --environment DEV \
  --output-dir /tmp/hedp-snowflake-preview
terraform -chdir=infrastructure/terraform/environments/dev init -backend=false
terraform -chdir=infrastructure/terraform/environments/dev validate
```

Rendering is a deterministic review artifact, not an apply. See the [deployment runbook](docs/operations/snowflake-deployment.md) before any connected execution.

Run the interoperability sample locally:

```bash
healthcare-platform interoperability process-batch \
  --input-dir data/samples/small/relational \
  --output-dir /tmp/interoperability --seed 42
healthcare-platform interoperability validate-fhir --input-dir /tmp/interoperability/fhir
healthcare-platform interoperability validate-hl7 --input-dir /tmp/interoperability/hl7
```

## Limitations

The generator uses compact portfolio code sets rather than authoritative clinical terminology. Large-profile configuration exists but has not been executed; current relationship assembly is in-memory and must be partitioned before million-patient benchmarking. The Snowflake foundation has not been planned or applied against a live account, and there are no source loads, dbt domain models, live security policies, dashboards, governed research workflows, or cloud deployment evidence.

Current non-goals also include formal FHIR conformance, HL7 parsing, billing/finance generation, revenue calculations, Airflow DAGs, Dataiku projects or models, feature-store implementation, Fabric/Power BI artifacts, broader platform Terraform and multi-region deployment. Target-state documentation does not turn these into implemented capabilities.

## Portfolio positioning

This is an evidence-led engineering portfolio: each later capability must be implemented, tested, measured, and captured before it is claimed. The architecture prioritises practical Snowflake/dbt depth while keeping business rules portable where reasonable. See the [evidence plan](docs/evidence/evidence-plan.md).

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing the project. Report security concerns using [SECURITY.md](SECURITY.md). This repository is licensed under the [MIT License](LICENSE).
