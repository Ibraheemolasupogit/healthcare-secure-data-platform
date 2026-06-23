# Repository realignment plan

## Purpose and verified baseline

This plan maps the existing Healthcare Secure Data Platform to the expanded Healthcare Enterprise Data Platform target without replacing working assets. Milestone 1 is complete. Milestone 2 is **complete with documented limitations**: the generator and packaged CLI validate successfully, the 100-patient sample contains 1,090 rows across 15 datasets, 19 tests pass with 93% coverage, and deterministic canonical outputs match across repeated runs. Large-profile execution remains intentionally unproven and the FHIR-inspired bundle is not conformant FHIR. A prior editable-install `.pth` issue was isolated to the local macOS Python environment; tests retain explicit `src` layout configuration and the locally built wheel/installed CLI at version `0.2.0` pass. No machine-specific import workaround is added.

Status terms in this document mean: **Implemented** is working and validated; **Partially implemented** is useful working capability with acknowledged gaps; **Placeholder only** is intentional structure or design text without runtime capability; **Not implemented** means no asset exists; **Deferred intentionally** means sequenced to a named future milestone.

## A. Existing capability inventory

| Existing path/component | Current purpose | Status and quality | Dependencies / consumers | Revised milestone | Action |
|---|---|---|---|---|---|
| `README.md`, root standards | Project contract and developer entry point | Implemented; accurate through M2 | All contributors | 1–17 | EXTEND |
| `src/healthcare_platform/synthetic` | Deterministic domain generation, writing, validation and provenance | Implemented; typed, tested, 93% suite coverage | CLI, samples, future ingestion | 2; input to 4–9 | KEEP |
| `synthetic/generators/foundational.py` | Organisations, locations, providers and patients | Implemented and internally consistent | Clinical generators, future core model | 2, 6 | KEEP |
| `synthetic/generators/care.py` | Encounters, admissions, appointments, pathways, clinical/pathology/medication events | Implemented; synthetic portfolio semantics | Future interoperability and dbt healthcare core | 2, 5–6 | KEEP |
| `synthetic/generators/governance.py` | Consent, cohort, audit and negative quality events | Implemented; bounded research semantics | Future governance and research products | 2, 14 | KEEP |
| `synthetic/schemas/catalog.py` | Versioned field/key/classification catalogue | Implemented; schema `1.0.0` | Writers, validator, future source contracts | 2, 5–8 | KEEP |
| `code_sets.py` | Controlled synthetic healthcare vocabularies | Implemented; deliberately non-authoritative | Generator and validator | 2; terminology mapping in 4 | KEEP |
| `identifiers.py`, `random_streams.py` | Stable IDs and isolated seeded streams | Implemented; no unstable hashes | All synthetic domains | 2, 7 | KEEP |
| `profiles.py`, `config/synthetic` | Small/medium/large volumes | Partially implemented; large configured but not executed | Generator, future benchmark | 2, 17 | KEEP |
| `manifest.py`, `service.py` | Checksums, provenance and run orchestration | Implemented; volatile metadata correctly excluded from deterministic inventory | Evidence, future ingestion | 2, 4–5, 17 | KEEP |
| `data/samples/small` | Reviewed CSV, JSON Lines and FHIR-inspired sample | Implemented and validated; 704 KB | Tests, future ingestion fixtures | 2, 4–6 | KEEP |
| `data/negative_tests` contract | Separate intentional-defect output | Implemented but ignored by Git as designed | Validator and future quarantine tests | 2, 4–5 | KEEP |
| `src/healthcare_platform/cli.py` | `info`, `generate`, `validate-data`, `describe-profile`, `list-datasets` | Implemented and packaged at `0.2.0` | Local/CI users | 1–2 | KEEP |
| `tests/unit`, `tests/integration` | Determinism, schema, rules, CLI, manifest and overwrite tests | Implemented; 19 passing | CI | Every milestone | EXTEND |
| `docs/data-model`, `docs/operations`, `docs/evidence` | M2 contracts, procedures and evidence | Implemented and consistent | Contributors and reviewers | 2, 17 | KEEP |
| `dbt` | One parseable transformation project and conventions | Placeholder only; deliberately no fake models | Future Snowflake sources/products | 5–9 | EXTEND |
| `snowflake` | Modular numbered SQL deployment design | Placeholder only; useful responsibility split | Future Terraform/deployment role | 3–5, 14–16 | EXTEND |
| `infrastructure/terraform` | No-resource module, environments and provider example | Placeholder only; format/validate passes | Future Snowflake and platform infrastructure | 3, 15–16 | EXTEND |
| `infrastructure/docker`, `compose.yml` | Reproducible local validation image | Implemented foundation; no platform emulator | Developers and CI | 1 onward | KEEP |
| `.github/workflows` | Credential-free quality/security gates | Implemented foundation; no deployment jobs | Pull requests | 1, expanded in 3–17 | EXTEND |
| `orchestration/airflow` | Boundary documentation | Placeholder only; no DAG | Future cross-platform workflows | 10 | EXTEND |
| `dataiku` | Governed research workflow contract | Placeholder only; no flow/runtime | Future trusted Snowflake products | 11 | EXTEND |
| `fabric`, `fabric/power_bi` | Consumption boundary documentation | Placeholder only; no semantic model/report | Future trusted dbt products | 13 | EXTEND |
| `monitoring` | Intended telemetry sources | Placeholder only | Every runtime component | 9–17 | EXTEND |
| `reports`, `outputs` | Future evidence/report destinations | Placeholder only with handling guidance | Validation and portfolio evidence | 17 | KEEP |
| Security/governance docs and ADRs | Threats, RBAC, classification and research controls | Partially implemented as design; no live controls | M3, M14–16 | 1, 14 | EXTEND |
| Billing/finance domains | No schemas, generator, sample or transformation | Not implemented | Future clinical activity and contracts | 7–9 | ADD NEW |
| FHIR parser / HL7 parser | No parser, validation or quarantine | Not implemented; inspiration-only fixture exists | Future RAW ingestion | 4 | ADD NEW |
| Feature store | No model, metadata or serving implementation | Not implemented | Trusted dbt products and Dataiku | 12 | ADD NEW |
| Multi-region | No topology, RTO/RPO or runbook | Not implemented | Deployed platform and Terraform | 16 | ADD NEW |

## B. Preservation map

The following are protected extension points and must remain intact:

- synthetic generators and their domain ownership in `src/healthcare_platform/synthetic/generators`;
- schema catalogue, version `1.0.0`, classifications, primary keys and foreign keys;
- identifier prefixes, ordinal allocation and SHA-256-derived random streams;
- controlled code sets and the explicit statement that they are not authoritative NHS terminology;
- profile configuration and small/medium/large meanings;
- structural, referential, temporal and healthcare business-rule validation;
- manifest, Git provenance, configuration hash, file checksums and deterministic checksum scope;
- all five CLI commands and existing import paths;
- committed small sample, validation reports and FHIR-inspired non-conformance disclaimer;
- ignored negative-test output contract and defect-event traceability;
- unit/integration tests and CI quality workflows;
- existing architecture, security, governance, operations, evidence and ADR documents;
- the single dbt project, its layer directories and parse-only profile;
- numbered Snowflake concern structure and responsibility boundaries;
- Terraform environment/module pattern and inactive provider example;
- Docker/Compose local validation path.

Future work extends these assets in place. A rename or move requires dependency discovery, compatibility handling and an explicit migration decision; resemblance to a target diagram is not sufficient reason.

## C. Old-to-new architecture mapping

| Existing capability | Expanded target role | Direction |
|---|---|---|
| Patient/organisation/provider generators | Synthetic healthcare source systems | KEEP |
| Encounter, admission, appointment and pathway datasets | Clinical and operational source domains | KEEP; EXTEND only through versioned schema changes |
| Clinical event referral/procedure categories | Early clinical activity coverage | KEEP; add explicit treatment/procedure entities only when grain requires it |
| FHIR-inspired bundle | Future interoperability fixtures | KEEP as non-conformant test input; never call it parsed or conformant FHIR |
| CSV and JSON Lines samples | Batch and semi-structured source fixtures | KEEP for RAW ingestion tests |
| Schema catalogue and code sets | Canonical source contracts and future terminology mapping inputs | KEEP |
| Validator and negative fixtures | Ingestion quarantine and dbt quality controls | KEEP; reuse rule intent without duplicating definitions |
| Snowflake scaffolding | Governed central platform foundation | PRESERVE and implement incrementally |
| dbt skeleton | One transformation project for staging, healthcare core, billing, controls, marts and semantics | PRESERVE and extend |
| Airflow placeholder | Cross-platform orchestration only | PRESERVE boundary; implement later |
| Dataiku scaffold | Governed analytics/ML over trusted products | PRESERVE boundary; never bypass dbt products |
| Fabric/Power BI scaffold | Certified semantic consumption and reporting | PRESERVE boundary; never rebuild curated models |
| Terraform scaffold | Repeatable infrastructure and environment design | PRESERVE; activate by reviewed modules |
| Security/governance documentation | Future executable controls and evidence | KEEP and strengthen later |

## D. Gap analysis

| Target capability | Current classification | Gap / dependency | Planned milestone |
|---|---|---|---|
| Treatments and procedures | Partially implemented | `clinical_events` can carry categories, but no explicit grain/schema | 6 assessment; 7 extension if source grain required |
| Services/products/tariffs/contracts | Not implemented | Billing source contracts absent | 7 |
| Claims, invoices and invoice lines | Not implemented | No synthetic finance source or rules | 7–8 |
| Payment attempts/payments/refunds/adjustments/failed payments | Not implemented | No payment lifecycle model | 7–8 |
| Billing exceptions/revenue/outstanding balances | Not implemented | No canonical calculations or reconciliation | 8–9 |
| Billing reconciliation/revenue assurance | Not implemented | Requires billing transformations and control totals | 9 |
| FHIR parsing/conformance | Not implemented | Existing output is explicitly inspiration-only | 4 |
| HL7 parsing | Not implemented | No messages, parser or validation | 4 |
| Rejected-message quarantine | Not implemented | Requires interoperability ingestion contract | 4 |
| Snowflake deployment | Placeholder only | SQL/Terraform scaffolds have no remote resources | 3 |
| dbt staging | Placeholder only | Project parses but contains no source/model | 5 |
| Healthcare core dimensional model | Not implemented | Requires staged clinical sources | 6 |
| Finance dimensional model | Not implemented | Requires M7 synthetic sources and staging | 8 |
| Airflow | Placeholder only | No cross-platform runtime yet | 10 |
| Dataiku analytics/ML | Placeholder only | Requires governed trusted products | 11 |
| Governed feature store | Not implemented | Requires core/billing data products and feature ownership | 12 |
| Fabric/Power BI | Placeholder only | Requires certified semantic interfaces | 13 |
| Executable security controls | Partially implemented as design | RBAC/policy SQL not deployed or persona-tested | 3, 14 |
| Operational observability | Placeholder only | No runtime telemetry, SLOs or alert routes | 9–17 incrementally |
| Terraform resources | Placeholder only | Provider example inactive; no remote state/resource plan | 3, 15 |
| Multi-region architecture | Not implemented | Needs workload state, RTO/RPO and platform deployment decisions | 16 |
| Operational runbooks | Partially implemented | Generation procedures exist; platform recovery/incident runbooks absent | 16–17 |
| Portfolio evidence | Partially implemented | M2 evidence exists; no cloud/deployment evidence | Every milestone; consolidated in 17 |

Billing and finance synthetic entities should be introduced in a focused **Milestone 7**, immediately before billing dbt work. Adding them before Snowflake foundation would reopen completed Milestone 2 and delay validation of the central platform. Adding them inside the billing dbt milestone would couple source generation to transformation and obscure ownership. The M7 boundary preserves the existing clinical generator while adding versioned finance source domains only after core clinical grains have been proven.

## E. Non-cannibalisation risk register

| Risk | Likelihood | Impact | Affected assets | Prevention control | Future validation gate |
|---|---|---:|---|---|---|
| Duplicate patient model | Medium | Critical | Patient schema, core dbt model | Existing schema is source contract; one dbt conformed definition | Grain/key lineage review in M6 |
| Duplicate encounter definition | Medium | High | Encounter/admission/appointment generators | Document grains; version rather than fork | Reconciliation tests in M5–6 |
| Duplicate generator | Low | High | Entire synthetic package | Extend current package only; architectural review for new roots | Repo path/entry-point check in CI |
| Conflicting identifiers | Medium | High | All foreign keys/manifests | Central `identifiers.py`; no ad hoc IDs | Contract test per new dataset |
| Competing billing schemas | High | High | Future M7/M8 | One source catalogue extension and one dbt domain | Schema ownership approval in M7 |
| Separate revenue calculations | High | Critical | dbt, Dataiku, Fabric, Power BI | dbt owns revenue recognition logic | Cross-consumer reconciliation in M9/13 |
| Duplicate tariff logic | High | Critical | Contracts, invoices, reports | dbt canonical effective-dated tariff assignment | Known-case tariff tests in M8 |
| Conflicting code sets | Medium | High | Synthetic and interoperability layers | Central source codes plus explicit mapping/version tables | Terminology coverage tests in M4–5 |
| Broken CLI/import contracts | Low | High | Local workflows and CI | Backward-compatible commands; package tests | Wheel/CLI smoke test each release |
| Premature moves/renames | Medium | Medium | Docs, imports, workflow paths | Dependency inventory and migration ADR first | Link/import/workflow checks |
| Duplicate dbt projects | Medium | High | Lineage and deployments | `dbt/` remains the single project | CI asserts one `dbt_project.yml` |
| Duplicate Snowflake deployment structures | Medium | High | SQL and Terraform ownership | Existing concern structure plus Terraform resource authority | Plan/object inventory review in M3 |
| Dataiku bypasses governed dbt products | Medium | Critical | Research/ML access | Read only approved marts/features | Connection and lineage test in M11 |
| Fabric recreates curated models | High | High | Semantic model | Certified dbt semantic interfaces only | Measure/source reconciliation in M13 |
| Power BI becomes transformation layer | High | High | Reports and finance metrics | Presentation-only calculations policy | Report-local logic inventory in M13 |
| Feature engineering bypasses trusted products | Medium | Critical | Feature store/Dataiku | Features sourced from governed dbt products | Point-in-time lineage test in M12 |
| Airflow duplicates native schedules | Medium | High | Tasks/dbt jobs/DAGs | ADR 0003 boundary and single trigger owner | Scheduler ownership test in M10 |
| Empty folders mistaken for implementation | High | Medium | Platform scaffolds | Explicit status labels and evidence-required claims | README/evidence review each milestone |
| Architecture claims exceed evidence | Medium | High | Portfolio credibility | Status taxonomy and claim-to-evidence index | M17 clean-room audit |

## F. Single-source-of-truth ownership

| Definition | Planned owner | Consumers / prohibited duplication |
|---|---|---|
| Patient source shape | Versioned synthetic/interoperability source contract | dbt stages it; tools do not redefine it |
| Conformed patient | dbt healthcare core | Dataiku/Fabric/Power BI consume it |
| Encounter and appointment definitions | Source contract for source grain; dbt for conformed business grain | No report-local reclassification |
| Treatment/procedure definitions | Interoperability/source contract, conformed by dbt | Dataiku consumes governed representations |
| Billable activity | dbt billing domain using conformed clinical activity | No Dataiku/BI recreation |
| Tariff assignment | dbt effective-dated billing logic | Fabric/Power BI read assigned values |
| Invoice total | dbt billing domain, reconciled to synthetic source invoice | One certified calculation |
| Payment allocation | dbt billing domain | No dashboard-side allocation |
| Outstanding balance | dbt finance mart from invoices, allocations, refunds and adjustments | BI displays only |
| Revenue recognition | dbt finance policy model with versioned rule and finance owner | Dataiku may analyse, not redefine |
| Waiting-time calculation | dbt conformed pathway logic; generator provides expected source fixture | Reports consume certified measure |
| Consent status | Governed dbt consent model under governance owner | Row policies and research tools consume it |
| Reusable analytical features | Feature-store definitions over trusted dbt products | Dataiku authors through governed registration; online serving later |

Snowflake is the governed execution/storage platform, not a second owner of business definitions. SQL policies may enforce access but must not silently reinterpret domain rules.

## G. Revised milestone sequence

1. **Repository foundation — COMPLETE.** Preserve standards, architecture and toolchain.
2. **Synthetic healthcare data — COMPLETE WITH DOCUMENTED LIMITATIONS.** Preserve current clinical/operational generator and contracts.
3. **Snowflake foundation.** Deploy environment-scoped databases, schemas, warehouses, monitors and least-privilege roles using existing SQL/Terraform boundaries.
4. **FHIR and HL7 ingestion.** Add synthetic messages, parsers, validation, canonical mappings and quarantine; retain current FHIR-inspired bundle only as a labelled fixture.
5. **dbt staging layer.** Declare sources/freshness and source-aligned staging for batch and interoperability inputs.
6. **Healthcare core model.** Conform patient, organisation, provider, location, encounter, admission, appointment, pathway and clinical domains.
7. **Billing and finance synthetic-domain extension.** Extend the existing generator/catalog with services, products, tariffs, contracts, claims, invoices, payment lifecycle and exceptions—without forking clinical models.
8. **Billing and finance dbt domain.** Build tested billable activity, tariff, invoice, payment, balance and revenue models.
9. **Reconciliation and revenue assurance.** Add control totals, exception workflows, observability and financial evidence.
10. **Airflow orchestration.** Coordinate cross-platform dependencies, backfills and evidence without duplicating dbt/Snowflake scheduling.
11. **Dataiku workflows.** Use governed products for collaborative analytics, features, experiments and model monitoring.
12. **Governed feature store.** Define ownership, freshness, versioning and point-in-time-correct offline features; defer online serving until justified.
13. **Fabric and Power BI.** Publish certified semantic models and clinical/operational/financial reporting without transformation duplication.
14. **Governance and security implementation.** Complete masking, row access, pseudonymisation, consent, audit and separation-of-duties evidence.
15. **Terraform implementation and environment design.** Broaden repeatable provisioning to identity, storage, networking, secret integration and monitoring after resource designs are proven.
16. **Multi-region architecture and recovery runbooks.** Define data residency, failover, RTO/RPO, replication and recovery exercises.
17. **Portfolio evidence and polish.** Consolidate runbooks, benchmarks, CI/CD releases, claim-to-evidence mapping and clean-room reproduction.

The original 15-milestone roadmap is deliberately revised rather than concealed: native ingestion, quality, security, performance and CI responsibilities are redistributed into dependency-led milestones; billing/finance, interoperability, feature store and multi-region capabilities add explicit boundaries. Detailed deliverables and exclusions are maintained in `docs/roadmap/milestones.md`.
