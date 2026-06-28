# Healthcare Secure Data Platform

A production-style, synthetic-only Healthcare Enterprise Data Platform portfolio for clinical, operational, research and financial data engineering. Snowflake remains the target governed data platform and dbt remains the transformation, testing, documentation, lineage and business-logic centre of gravity.

> **Status — Milestone 9 complete locally:** dbt now includes governed billing/finance calculations plus reconciliation, exception lifecycle, prioritisation, remediation status, revenue-at-risk summaries and deterministic assurance evidence metadata. Snowflake execution, marts and later platform integrations remain planned.

## Why this project exists

Healthcare teams need trusted clinical, operational and financial data products without widening access to identifying or sensitive data. The target platform separates interoperability, ingestion, transformation, governance, billing controls, analytics/ML, research access, reporting and orchestration so each can evolve without bypassing controls. It is intended for data and analytics engineers, platform and security engineers, data-quality and finance-control analysts, clinical/operational analysts, approved researchers, data scientists and BI consumers.

## Architecture at a glance

Files and JSON land immutably in **RAW**; dbt standardises them in **STAGING**, builds reusable logic in **INTERMEDIATE**, publishes governed entities in **CURATED**, and produces purpose-specific **MART** and **SEMANTIC** interfaces. Snowflake supplies storage, isolated compute, native ingestion/change processing, access controls, sharing, recovery, monitoring, and cost controls. dbt owns SQL transformation logic and its tests, contracts, lineage, and documentation.

Python now generates synthetic data and validates its structure and relationships. Future FHIR/HL7 and batch ingestion will validate and map source messages before Snowflake RAW. Airflow will coordinate cross-platform work only; Snowflake Tasks and dbt remain responsible for their own scheduling domains. Dataiku will consume governed products for collaborative analytics and ML. A governed feature store will register reusable, point-in-time-correct features. Fabric and Power BI will consume certified semantic products rather than recreate transformation logic. Terraform will provision infrastructure, and GitHub Actions will enforce quality and security gates.

Detailed boundaries are documented in [component responsibilities](docs/architecture/component-responsibilities.md), the [target-state architecture](docs/architecture/target-state-architecture.md), and the [repository realignment plan](docs/architecture/repository-realignment-plan.md).

## Implementation status by capability

| Capability | Responsibility | Current status |
|---|---|---|
| Python synthetic platform | Deterministic source data, schemas, validation and provenance | **Implemented locally** for M2 clinical/operational/research domains and M7 billing/finance source domains |
| Interoperability | Synthetic FHIR-inspired/HL7 generation, parsing, envelopes and quarantine | **Implemented locally for the bounded M4 subset** |
| Snowflake | Governed central storage/compute, RAW-to-serving layers and access enforcement | **M3 foundation declared and statically validated; not deployed** |
| dbt | Transformation, testing, documentation, lineage, dimensional models, contracts, assurance controls and business logic | **M5 sources/staging, M6 healthcare core, M8 billing/finance and M9 assurance controls implemented locally; marts planned** |
| FHIR and HL7 | Source interoperability, validation, canonical mapping and quarantine | **Bounded synthetic FHIR-inspired and HL7 parsers implemented locally** |
| Airflow | Cross-platform orchestration, retries, backfills and failure handling | **Placeholder only; planned** |
| Dataiku | Governed analytics, feature engineering, ML, experiments and model monitoring | **Placeholder only; planned** |
| Feature store | Governed reusable features, ownership, freshness, versions and point-in-time correctness | **Not implemented; planned** |
| Fabric and Power BI | Certified semantic consumption and operational/financial/executive reporting | **Placeholder only; planned** |
| Terraform | Repeatable infrastructure, identity, storage, networking, secrets and monitoring | **Snowflake foundation module implemented; no apply performed** |
| Governance/security | RBAC, masking, pseudonymisation, row access, consent, retention and audit | **M3 roles/grants/tags declared; policies remain planned** |

## Local-first development

Developers can install the Python package, lint SQL/YAML/Terraform, and validate structure without a cloud account. Docker pins a small Python/dbt toolchain. Local work validates portable logic; Snowflake-only behaviour—RBAC, policies, Streams, Tasks, Snowpipe, cloning, Time Travel and warehouse economics—must later be tested in an isolated Snowflake development environment. See [local-first strategy](docs/architecture/local-first-strategy.md).

## Implemented synthetic healthcare domains

The generator covers organisations, locations, providers, patients, encounters, admissions/discharges, outpatient appointments, waiting-list pathways, clinical events, pathology results, medication events, research consent and cohorts, audit activity, controlled data-quality events, and billing/finance source entities for payers, services, products, tariffs, contracts, claims, invoices, payments, refunds, adjustments, exceptions, revenue events, balances and control totals. The committed sample uses 100 patients and proportionate related records. See the [synthetic data model](docs/data-model/synthetic-data-model.md) and [billing source model](docs/data-model/billing-source-model.md).

The billing and finance source fixtures now feed governed dbt billing/finance dimensions, facts, controls and Milestone 9 assurance outputs. Revenue-recognition policy, finance marts, external workflow orchestration and semantic/reporting outputs remain future work.

## Data and security principles

The target layers are `RAW → STAGING → INTERMEDIATE → CURATED → MART → SEMANTIC`. RAW is immutable and source-aligned; each later layer progressively standardises, resolves, governs, and serves data.

The design follows least privilege, workload isolation, encryption in transit/at rest, auditable access, data minimisation, and deny-by-default research access. Pseudonymisation replaces direct identifiers but remains reversible under control; anonymisation aims to prevent re-identification; tokenisation uses controlled substitutes; masking changes presentation by role; row policies filter records; encryption protects bytes. These are complementary—not interchangeable—controls.

**Synthetic data only:** real patient data, real NHS numbers, personal data, secrets, connection strings, and production credentials are prohibited from this repository.

## Milestones

- **Complete:** Milestone 1 repository foundation.
- **Complete with documented limitations:** Milestone 2 deterministic synthetic healthcare generation.
- **Complete locally; live evidence pending:** Milestone 3 Snowflake foundation.
- **Complete locally:** Milestone 4 FHIR and HL7 ingestion foundation.
- **Complete locally:** Milestone 5 dbt sources, freshness and source-aligned staging layer.
- **Complete locally:** Milestone 6 conformed healthcare core model.
- **Complete locally:** Milestone 7 billing and finance synthetic source extension.
- **Complete locally:** Milestone 8 governed billing and finance dbt domain.
- **Complete locally:** Milestone 9 reconciliation and revenue assurance controls.
- **Recommended next:** Milestone 10 Airflow orchestration.
- **Planned:** Milestones 10–17 add Airflow, Dataiku, feature store, Fabric/Power BI, executable governance, broader Terraform, multi-region recovery and portfolio evidence.

The original 15-milestone plan has been transparently realigned into a 17-milestone dependency-led [roadmap](docs/roadmap/milestones.md). [ADR 0009](docs/decisions/0009-expand-to-healthcare-enterprise-platform.md) records why.

## Repository map

| Path | Responsibility |
|---|---|
| `src/healthcare_platform` | Python CLI, generator, schemas, writers and validation |
| `data/samples/interoperability` | Reviewed FHIR-inspired, HL7, envelope, crosswalk and manifest samples |
| `config/synthetic` | Small, medium and large generation profiles |
| `data/samples/small` | Reviewed 100-patient synthetic sample and evidence |
| `dbt` | Sources, freshness metadata, staging models, healthcare core, billing/finance, assurance controls and dbt tests |
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
healthcare-platform list-datasets --domain billing
healthcare-platform validate-billing --input-dir data/generated/small
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

Validate the dbt Milestone 5 layer locally:

```bash
cd dbt
PATH="../.venv/bin:$PATH" dbt parse --profiles-dir . --no-partial-parse
cd ..
PYTHONPATH=src pytest tests/unit/test_dbt_milestone5.py
```

`dbt compile`, `dbt build`, `dbt source freshness` and `dbt docs generate` require an authorised Snowflake target; the committed placeholder profile is parse-only.

Validate the dbt Milestone 6 core guardrails locally:

```bash
PYTHONPATH=src pytest tests/unit/test_dbt_milestone6.py
```

Validate the dbt Milestone 9 assurance guardrails and evidence pack locally:

```bash
PYTHONPATH=src pytest tests/unit/test_dbt_milestone9.py
PYTHONPATH=src python -m healthcare_platform.cli assurance-evidence \
  --output-dir /tmp/m9-assurance-evidence --overwrite
```

## Limitations

The generator uses compact portfolio code sets rather than authoritative clinical terminology. Large-profile configuration exists but has not been executed; current relationship assembly is in-memory and must be partitioned before million-patient benchmarking. The Snowflake foundation has not been planned or applied against a live account, and there are no source loads, runtime-proven dbt builds, live security policies, dashboards, governed research workflows, or cloud deployment evidence.

Current non-goals also include formal FHIR conformance, formal revenue recognition, external revenue-assurance workflow orchestration, Airflow DAGs, Dataiku projects or models, feature-store implementation, Fabric/Power BI artifacts, broader platform Terraform and multi-region deployment. Target-state documentation does not turn these into implemented capabilities.

## Portfolio positioning

This is an evidence-led engineering portfolio: each later capability must be implemented, tested, measured, and captured before it is claimed. The architecture prioritises practical Snowflake/dbt depth while keeping business rules portable where reasonable. See the [evidence plan](docs/evidence/evidence-plan.md).

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing the project. Report security concerns using [SECURITY.md](SECURITY.md). This repository is licensed under the [MIT License](LICENSE).
