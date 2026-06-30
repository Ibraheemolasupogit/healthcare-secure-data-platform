"""Foundation command-line interface."""

import argparse
import importlib.util
import json
import platform
from dataclasses import replace
from datetime import date
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from healthcare_platform.assurance import write_evidence_pack
from healthcare_platform.config import load_settings, snowflake_credentials_present
from healthcare_platform.dataiku import run_reference_pipeline
from healthcare_platform.deployment import (
    build_deployment_evidence,
    detect_drift,
    evaluate_policy_gates,
    load_deployment_registry,
    validate_deployment_controls,
)
from healthcare_platform.deployment import (
    verify_evidence as verify_deployment_evidence,
)
from healthcare_platform.feature_store import build_reference_outputs, validate_registry
from healthcare_platform.governance import (
    build_governance_evidence,
    load_governance_registry,
)
from healthcare_platform.governance import (
    describe_policy as describe_governance_policy,
)
from healthcare_platform.governance import (
    evaluate_access as evaluate_governance_access,
)
from healthcare_platform.governance import (
    validate_registry as validate_governance_registry,
)
from healthcare_platform.governance import (
    verify_evidence as verify_governance_evidence,
)
from healthcare_platform.interoperability.config import (
    DEFAULT_CONFIG_PATH as DEFAULT_INTEROPERABILITY_CONFIG_PATH,
)
from healthcare_platform.interoperability.service import (
    DEFAULT_CANONICAL_INPUT,
    describe_contracts,
    generate_fhir,
    generate_hl7,
    generate_negative_corpus,
    process_batch,
    validate_corpus,
)
from healthcare_platform.logging_config import configure_logging
from healthcare_platform.operations import (
    build_operations_evidence,
    describe_drill,
    evaluate_health,
    load_operations_registry,
    simulate_drill,
    simulate_incident,
    validate_operations_registry,
)
from healthcare_platform.operations import (
    verify_evidence as verify_operations_evidence,
)
from healthcare_platform.powerbi import (
    build_reference_outputs as build_powerbi_reference_outputs,
)
from healthcare_platform.powerbi import (
    describe_measure as describe_powerbi_measure,
)
from healthcare_platform.powerbi import (
    load_powerbi_metadata,
    validate_model,
    verify_reference_outputs,
)
from healthcare_platform.recovery import (
    build_recovery_evidence,
    load_recovery_registry,
    simulate_failover,
    validate_recovery_registry,
)
from healthcare_platform.recovery import (
    describe_scenario as describe_recovery_scenario,
)
from healthcare_platform.recovery import (
    verify_evidence as verify_recovery_evidence,
)
from healthcare_platform.snowflake_foundation import (
    DEFAULT_CONFIG_PATH as DEFAULT_SNOWFLAKE_CONFIG_PATH,
)
from healthcare_platform.snowflake_foundation import (
    DEFAULT_INVENTORY_PATH as DEFAULT_SNOWFLAKE_INVENTORY_PATH,
)
from healthcare_platform.snowflake_foundation import (
    load_foundation,
    render_preview,
    validate_foundation,
    write_inventory,
)
from healthcare_platform.synthetic.profiles import DEFAULT_PROFILE_PATH, load_profile
from healthcare_platform.synthetic.schemas import DATASET_ORDER, SCHEMAS
from healthcare_platform.synthetic.service import generate_to_directory, validate_directory

PROJECT_NAME = "Healthcare Secure Data Platform"
BILLING_DATASETS = {
    "payers",
    "services",
    "products",
    "tariffs",
    "contracts",
    "billable_activity",
    "claims",
    "claim_lines",
    "invoices",
    "invoice_lines",
    "payment_attempts",
    "payments",
    "refunds",
    "adjustments",
    "billing_exceptions",
    "revenue_events",
    "outstanding_balances",
    "daily_control_totals",
}


def dbt_available() -> bool:
    """Return whether dbt Core is importable in the current environment."""
    return importlib.util.find_spec("dbt") is not None


def build_parser() -> argparse.ArgumentParser:
    """Build the command parser."""
    parser = argparse.ArgumentParser(prog="healthcare-platform")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("info", help="show safe local environment diagnostics")
    generate = subparsers.add_parser("generate", help="generate deterministic synthetic datasets")
    generate.add_argument("--profile", choices=("small", "medium", "large"), default="small")
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--reference-date", type=date.fromisoformat, default=date(2025, 1, 1))
    generate.add_argument("--output-dir", type=Path)
    generate.add_argument("--format", choices=("all", "csv", "jsonl"), default="all")
    generate.add_argument(
        "--include",
        choices=("all", "billing"),
        default="all",
        help=(
            "dataset family to include; billing is generated through the canonical source portfolio"
        ),
    )
    generate.add_argument("--patient-count", type=int)
    generate.add_argument("--inject-defects", action="store_true")
    generate.add_argument("--negative-test-mode", action="store_true")
    generate.add_argument("--overwrite", action="store_true")
    generate.add_argument("--config", type=Path, default=DEFAULT_PROFILE_PATH)
    validate_parser = subparsers.add_parser("validate-data", help="validate a generated output")
    validate_parser.add_argument("--input-dir", type=Path, required=True)
    validate_billing = subparsers.add_parser(
        "validate-billing", help="validate generated billing and finance source outputs"
    )
    validate_billing.add_argument("--input-dir", type=Path, required=True)
    describe = subparsers.add_parser(
        "describe-profile", help="show profile configuration and estimates"
    )
    describe.add_argument("profile", choices=("small", "medium", "large"))
    describe.add_argument("--config", type=Path, default=DEFAULT_PROFILE_PATH)
    list_datasets = subparsers.add_parser(
        "list-datasets", help="list canonical datasets and schema versions"
    )
    list_datasets.add_argument("--domain", choices=("all", "billing"), default="all")
    describe_schema = subparsers.add_parser("describe-schema", help="show one dataset schema")
    describe_schema.add_argument("dataset", choices=DATASET_ORDER)
    generate_negative = subparsers.add_parser(
        "generate-negative", help="generate deterministic negative synthetic source fixtures"
    )
    generate_negative.add_argument("--domain", choices=("billing",), default="billing")
    generate_negative.add_argument(
        "--profile", choices=("small", "medium", "large"), default="small"
    )
    generate_negative.add_argument("--seed", type=int, default=42)
    generate_negative.add_argument(
        "--reference-date", type=date.fromisoformat, default=date(2025, 1, 1)
    )
    generate_negative.add_argument(
        "--output-dir", type=Path, default=Path("data/negative_tests/billing")
    )
    generate_negative.add_argument("--overwrite", action="store_true")
    generate_negative.add_argument("--config", type=Path, default=DEFAULT_PROFILE_PATH)
    snowflake_validate = subparsers.add_parser(
        "snowflake-validate", help="statically validate the credential-free Snowflake foundation"
    )
    snowflake_validate.add_argument("--config", type=Path, default=DEFAULT_SNOWFLAKE_CONFIG_PATH)
    snowflake_validate.add_argument(
        "--inventory", type=Path, default=DEFAULT_SNOWFLAKE_INVENTORY_PATH
    )
    snowflake_inventory = subparsers.add_parser(
        "snowflake-inventory", help="write deterministic declared-object inventory"
    )
    snowflake_inventory.add_argument("--config", type=Path, default=DEFAULT_SNOWFLAKE_CONFIG_PATH)
    snowflake_inventory.add_argument(
        "--output", type=Path, default=DEFAULT_SNOWFLAKE_INVENTORY_PATH
    )
    snowflake_render = subparsers.add_parser(
        "snowflake-render", help="render non-deploying Snowflake validation previews"
    )
    snowflake_render.add_argument("--environment", choices=("DEV", "TEST", "PROD"), default="DEV")
    snowflake_render.add_argument("--config", type=Path, default=DEFAULT_SNOWFLAKE_CONFIG_PATH)
    snowflake_render.add_argument("--output-dir", type=Path, default=Path("outputs/snowflake/dev"))
    snowflake_render.add_argument("--overwrite", action="store_true")
    interoperability = subparsers.add_parser(
        "interoperability", help="generate and validate synthetic interoperability payloads"
    )
    interop_commands = interoperability.add_subparsers(dest="interop_command", required=True)
    for name, help_text in (
        ("generate-fhir", "generate deterministic FHIR-inspired resources and bundles"),
        ("generate-hl7", "generate deterministic synthetic HL7 v2 messages"),
    ):
        command = interop_commands.add_parser(name, help=help_text)
        command.add_argument("--input-dir", type=Path, default=DEFAULT_CANONICAL_INPUT)
        command.add_argument("--output-dir", type=Path, required=True)
        command.add_argument("--config", type=Path, default=DEFAULT_INTEROPERABILITY_CONFIG_PATH)
        command.add_argument("--overwrite", action="store_true")
    for name, source_format in (("validate-fhir", "FHIR"), ("validate-hl7", "HL7V2")):
        command = interop_commands.add_parser(name, help=f"validate {source_format} payloads")
        command.add_argument("--input-dir", type=Path, required=True)
        command.add_argument("--report-dir", type=Path)
        command.add_argument("--config", type=Path, default=DEFAULT_INTEROPERABILITY_CONFIG_PATH)
    batch = interop_commands.add_parser(
        "process-batch", help="build deterministic local ingestion artefacts"
    )
    batch.add_argument("--input-dir", type=Path, default=DEFAULT_CANONICAL_INPUT)
    batch.add_argument("--output-dir", type=Path, default=Path("data/generated/interoperability"))
    batch.add_argument("--config", type=Path, default=DEFAULT_INTEROPERABILITY_CONFIG_PATH)
    batch.add_argument("--seed", type=int, default=42)
    batch.add_argument("--overwrite", action="store_true")
    negative = interop_commands.add_parser(
        "generate-negative", help="generate deterministic rejected-payload fixtures"
    )
    negative.add_argument("--output-dir", type=Path, required=True)
    negative.add_argument("--overwrite", action="store_true")
    inspect_quarantine = interop_commands.add_parser(
        "inspect-quarantine", help="summarise local quarantine records"
    )
    inspect_quarantine.add_argument("--input-dir", type=Path, required=True)
    interop_commands.add_parser(
        "describe-contracts", help="print Snowflake raw-layer load contracts"
    )
    assurance_evidence = subparsers.add_parser(
        "assurance-evidence",
        help="write a deterministic local Milestone 9 assurance evidence pack",
    )
    assurance_evidence.add_argument("--output-dir", type=Path, required=True)
    assurance_evidence.add_argument("--overwrite", action="store_true")
    dataiku_reference = subparsers.add_parser(
        "dataiku-reference",
        help="run the deterministic local Milestone 11 Dataiku reference pipeline",
    )
    dataiku_reference.add_argument("--input", type=Path, required=True)
    dataiku_reference.add_argument("--output-dir", type=Path, required=True)
    dataiku_reference.add_argument("--overwrite", action="store_true")
    feature_store = subparsers.add_parser(
        "feature-store",
        help="inspect and validate the local governed feature-store registry",
    )
    feature_commands = feature_store.add_subparsers(dest="feature_store_command", required=True)
    feature_commands.add_parser("list-entities", help="list registered feature-store entities")
    feature_commands.add_parser("list-features", help="list registered reusable features")
    describe_feature = feature_commands.add_parser("describe-feature", help="describe one feature")
    describe_feature.add_argument("feature_id")
    feature_commands.add_parser("validate-registry", help="validate registry integrity")
    build_reference = feature_commands.add_parser(
        "build-reference",
        help="build deterministic historical and scoring retrieval reference outputs",
    )
    build_reference.add_argument("--output-dir", type=Path, required=True)
    build_reference.add_argument(
        "--fixture",
        type=Path,
        default=Path("feature_store/reference/fixtures/exception_events.csv"),
    )
    build_reference.add_argument("--overwrite", action="store_true")
    powerbi = subparsers.add_parser(
        "powerbi",
        help="inspect and validate local Power BI semantic-model metadata",
    )
    powerbi_commands = powerbi.add_subparsers(dest="powerbi_command", required=True)
    powerbi_commands.add_parser("validate-model", help="validate semantic model metadata")
    powerbi_commands.add_parser("list-tables", help="list semantic model tables")
    powerbi_commands.add_parser("list-measures", help="list central semantic measures")
    powerbi_commands.add_parser("list-kpis", help="list KPI definitions")
    powerbi_commands.add_parser("list-reports", help="list thin-report specifications")
    describe_measure_command = powerbi_commands.add_parser(
        "describe-measure", help="describe one measure"
    )
    describe_measure_command.add_argument("measure_id")
    generate_reference_command = powerbi_commands.add_parser(
        "generate-reference",
        help="generate deterministic local Power BI reference metadata outputs",
    )
    generate_reference_command.add_argument(
        "--output-dir", type=Path, default=Path("powerbi/reference")
    )
    generate_reference_command.add_argument("--overwrite", action="store_true")
    verify_reference_command = powerbi_commands.add_parser(
        "verify-reference", help="verify generated Power BI reference checksums"
    )
    verify_reference_command.add_argument(
        "--output-dir", type=Path, default=Path("powerbi/reference")
    )
    governance = subparsers.add_parser(
        "governance",
        help="validate and simulate the local governance-control registry",
    )
    governance_commands = governance.add_subparsers(dest="governance_command", required=True)
    governance_commands.add_parser("validate-registry", help="validate governance registry")
    governance_commands.add_parser("list-personas", help="list governed personas")
    governance_commands.add_parser("list-policies", help="list access policies")
    describe_policy_command = governance_commands.add_parser(
        "describe-policy", help="describe one access policy"
    )
    describe_policy_command.add_argument("policy_id")
    evaluate_access_command = governance_commands.add_parser(
        "evaluate-access", help="simulate a deterministic access decision"
    )
    evaluate_access_command.add_argument("--persona", required=True)
    evaluate_access_command.add_argument("--purpose", required=True)
    evaluate_access_command.add_argument("--environment", required=True)
    evaluate_access_command.add_argument("--domain", required=True)
    evaluate_access_command.add_argument("--object", dest="object_name", required=True)
    evaluate_access_command.add_argument("--operation", required=True)
    evaluate_access_command.add_argument("--sensitivity", required=True)
    evaluate_access_command.add_argument("--consent-state", default="not_applicable")
    evaluate_access_command.add_argument("--export-request", action="store_true")
    generate_governance = governance_commands.add_parser(
        "generate-evidence", help="generate deterministic local governance evidence"
    )
    generate_governance.add_argument(
        "--output-dir", type=Path, default=Path("governance/reference")
    )
    generate_governance.add_argument("--overwrite", action="store_true")
    verify_governance = governance_commands.add_parser(
        "verify-evidence", help="verify governance evidence checksums"
    )
    verify_governance.add_argument("--output-dir", type=Path, default=Path("governance/reference"))
    governance_commands.add_parser("coverage-report", help="show governance coverage counts")
    deployment = subparsers.add_parser(
        "deployment",
        help="validate local deployment-control metadata and evidence",
    )
    deployment_commands = deployment.add_subparsers(dest="deployment_command", required=True)
    deployment_commands.add_parser("validate", help="validate deployment-control registry")
    deployment_commands.add_parser("evaluate-policy-gates", help="evaluate local policy gates")
    deployment_commands.add_parser("detect-drift", help="run local deterministic drift simulation")
    deployment_commands.add_parser("generate-release", help="print local release metadata")
    deployment_commands.add_parser("generate-manifests", help="print local deployment manifests")
    deployment_commands.add_parser("validate-plan-metadata", help="validate static plan contract")
    generate_deployment = deployment_commands.add_parser(
        "generate-evidence", help="generate deterministic local deployment evidence"
    )
    generate_deployment.add_argument(
        "--output-dir", type=Path, default=Path("deployment/reference")
    )
    generate_deployment.add_argument("--overwrite", action="store_true")
    verify_deployment = deployment_commands.add_parser(
        "verify-evidence", help="verify deployment evidence checksums"
    )
    verify_deployment.add_argument("--output-dir", type=Path, default=Path("deployment/reference"))
    recovery = subparsers.add_parser(
        "recovery",
        help="validate and simulate local recovery controls",
    )
    recovery_commands = recovery.add_subparsers(dest="recovery_command", required=True)
    recovery_commands.add_parser("validate-registry", help="validate recovery registry")
    recovery_commands.add_parser("list-tiers", help="list recovery tiers")
    recovery_commands.add_parser("list-scenarios", help="list recovery scenarios")
    describe_recovery = recovery_commands.add_parser(
        "describe-scenario", help="describe one recovery scenario"
    )
    describe_recovery.add_argument("scenario_id")
    simulate_recovery = recovery_commands.add_parser(
        "simulate-failover", help="run deterministic local failover simulation"
    )
    simulate_recovery.add_argument("--scenario-id", default="primary_region_unavailable")
    recovery_commands.add_parser("validate-recovery", help="validate recovery manifest metadata")
    generate_recovery = recovery_commands.add_parser(
        "generate-evidence", help="generate deterministic local recovery evidence"
    )
    generate_recovery.add_argument("--output-dir", type=Path, default=Path("recovery/reference"))
    generate_recovery.add_argument("--overwrite", action="store_true")
    verify_recovery = recovery_commands.add_parser(
        "verify-evidence", help="verify recovery evidence checksums"
    )
    verify_recovery.add_argument("--output-dir", type=Path, default=Path("recovery/reference"))
    operations = subparsers.add_parser(
        "operations",
        help="validate local operational-readiness controls and simulations",
    )
    operations_commands = operations.add_subparsers(dest="operations_command", required=True)
    operations_commands.add_parser("validate-registry", help="validate operations registry")
    operations_commands.add_parser("list-services", help="list registered operational services")
    operations_commands.add_parser("list-slos", help="list synthetic SLO targets")
    operations_commands.add_parser("list-drills", help="list local recovery drills")
    describe_operations_drill = operations_commands.add_parser(
        "describe-drill", help="describe one recovery-drill definition"
    )
    describe_operations_drill.add_argument("drill_id")
    operations_commands.add_parser("evaluate-health", help="evaluate local synthetic health")
    operations_commands.add_parser("simulate-incident", help="simulate local incident triage")
    operations_commands.add_parser("simulate-drill", help="simulate local recovery drill")
    generate_operations = operations_commands.add_parser(
        "generate-evidence", help="generate deterministic local operations evidence"
    )
    generate_operations.add_argument(
        "--output-dir", type=Path, default=Path("operations/reference")
    )
    generate_operations.add_argument("--overwrite", action="store_true")
    verify_operations = operations_commands.add_parser(
        "verify-evidence", help="verify operations evidence checksums"
    )
    verify_operations.add_argument("--output-dir", type=Path, default=Path("operations/reference"))
    return parser


def info() -> int:
    """Print diagnostics without revealing secret values."""
    settings = load_settings()
    configure_logging(settings.log_level)
    values = {
        "project": PROJECT_NAME,
        "environment": settings.environment,
        "python_version": platform.python_version(),
        "execution_mode": settings.execution_mode,
        "snowflake_credentials_configured": snowflake_credentials_present(),
        "dbt_available": dbt_available(),
    }
    for key, value in values.items():
        print(f"{key}: {value}")
    return 0


def _generate(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile, args.config).with_patient_count(args.patient_count)
    if args.format != "all":
        profile = replace(profile, output_formats=(args.format,))
    default_root = Path("data/negative_tests" if args.negative_test_mode else "data/generated")
    output_dir = args.output_dir or default_root / profile.name
    result = generate_to_directory(
        profile=profile,
        seed=args.seed,
        reference_date=args.reference_date,
        output_dir=output_dir,
        overwrite=args.overwrite,
        inject_defects=args.inject_defects,
        negative_test_mode=args.negative_test_mode,
    )
    print(f"output_dir: {result.output_dir}")
    for dataset, count in result.row_counts.items():
        print(f"{dataset}: {count}")
    print(f"validation: {'PASS' if result.validation.valid else 'FAIL'}")
    return 0 if result.validation.valid or args.negative_test_mode else 1


def _describe(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile, args.config)
    print(
        json.dumps(
            {"configuration": profile.as_dict(), "estimated_rows": profile.estimated_rows()},
            indent=2,
        )
    )
    return 0


def _list_datasets(args: argparse.Namespace) -> int:
    names = DATASET_ORDER
    if args.domain == "billing":
        names = tuple(name for name in DATASET_ORDER if name in BILLING_DATASETS)
    for name in names:
        print(f"{name}: schema {SCHEMAS[name].schema_version} — {SCHEMAS[name].description}")
    return 0


def _validate_data(args: argparse.Namespace) -> int:
    report = validate_directory(args.input_dir)
    report.write(args.input_dir)
    print(f"validation: {'PASS' if report.valid else 'FAIL'}")
    print(f"rows_validated: {report.rows_validated}")
    print(f"issues: {len(report.issues)}")
    return 0 if report.valid else 1


def _describe_schema(args: argparse.Namespace) -> int:
    print(json.dumps(SCHEMAS[args.dataset].as_dict(), indent=2, sort_keys=True))
    return 0


def _generate_negative(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile, args.config)
    result = generate_to_directory(
        profile=profile,
        seed=args.seed,
        reference_date=args.reference_date,
        output_dir=args.output_dir,
        overwrite=args.overwrite,
        inject_defects=True,
        negative_test_mode=True,
    )
    print(f"negative_output_dir: {result.output_dir}")
    for dataset in DATASET_ORDER:
        if dataset in BILLING_DATASETS:
            print(f"{dataset}: {result.row_counts[dataset]}")
    print(f"validation: {'PASS' if result.validation.valid else 'FAIL'}")
    print(f"issues: {len(result.validation.issues)}")
    return 0


def _snowflake_validate(args: argparse.Namespace) -> int:
    result = validate_foundation(args.config, args.inventory)
    print(f"validation: {'PASS' if result.valid else 'FAIL'}")
    print(f"declared_objects: {result.inventory_count}")
    print(f"configuration_sha256: {result.configuration_sha256}")
    for warning in result.warnings:
        print(f"warning: {warning}")
    for error in result.errors:
        print(f"error: {error}")
    return 0 if result.valid else 1


def _snowflake_inventory(args: argparse.Namespace) -> int:
    path = write_inventory(load_foundation(args.config), args.output)
    print(f"inventory: {path}")
    return 0


def _snowflake_render(args: argparse.Namespace) -> int:
    files = render_preview(
        load_foundation(args.config), args.environment, args.output_dir, args.overwrite
    )
    print(f"output_dir: {args.output_dir}")
    for path in files:
        print(f"rendered: {path}")
    return 0


def _interoperability(args: argparse.Namespace) -> int:
    if args.interop_command == "generate-fhir":
        paths = generate_fhir(args.input_dir, args.output_dir, args.config, args.overwrite)
        print(f"generated_fhir_files: {len(paths)}")
        return 0
    if args.interop_command == "generate-hl7":
        paths = generate_hl7(args.input_dir, args.output_dir, args.config, args.overwrite)
        print(f"generated_hl7_messages: {len(paths)}")
        return 0
    if args.interop_command in {"validate-fhir", "validate-hl7"}:
        source_format = "FHIR" if args.interop_command == "validate-fhir" else "HL7V2"
        report = validate_corpus(args.input_dir, source_format, args.config, args.report_dir)
        print(f"validation: {'PASS' if report['valid'] else 'FAIL'}")
        print(f"payloads: {report['payload_count']}")
        return 0 if report["valid"] else 1
    if args.interop_command == "process-batch":
        manifest = process_batch(
            args.input_dir, args.output_dir, args.config, args.seed, args.overwrite
        )
        print(f"batch_id: {manifest['batch_id']}")
        print(f"accepted: {manifest['accepted_count']}")
        print(f"rejected: {manifest['rejected_count']}")
        return 0 if manifest["rejected_count"] == 0 else 1
    if args.interop_command == "generate-negative":
        generate_negative_corpus(args.output_dir, args.overwrite)
        print(f"negative_corpus: {args.output_dir}")
        return 0
    if args.interop_command == "inspect-quarantine":
        path = args.input_dir / "quarantine_records.json"
        records = json.loads(path.read_text(encoding="utf-8"))
        print(f"quarantine_records: {len(records)}")
        for disposition in sorted({record["disposition"] for record in records}):
            print(
                f"{disposition}: {sum(record['disposition'] == disposition for record in records)}"
            )
        return 0
    if args.interop_command == "describe-contracts":
        print(json.dumps(describe_contracts(), indent=2, sort_keys=True))
        return 0
    return 2


def _assurance_evidence(args: argparse.Namespace) -> int:
    pack = write_evidence_pack(args.output_dir, overwrite=args.overwrite)
    print(f"output_dir: {pack.output_dir}")
    print(f"manifest: {pack.manifest_path}")
    print(f"inventory: {pack.inventory_path}")
    print(f"summary: {pack.summary_path}")
    print(f"checksums: {pack.checksum_path}")
    return 0


def _dataiku_reference(args: argparse.Namespace) -> int:
    result = run_reference_pipeline(args.input, args.output_dir, overwrite=args.overwrite)
    print(f"output_dir: {result.output_dir}")
    print(f"run_manifest: {result.run_manifest}")
    print(f"baseline_metrics: {result.baseline_metrics}")
    print(f"candidate_metrics: {result.candidate_metrics}")
    print(f"selected_model: {result.selected_model}")
    print(f"prediction_sample: {result.prediction_sample}")
    print(f"model_card: {result.model_card}")
    print(f"checksums: {result.checksums}")
    return 0


def _feature_store(args: argparse.Namespace) -> int:
    if args.feature_store_command == "validate-registry":
        registry_result = validate_registry()
        print(json.dumps(registry_result, indent=2, sort_keys=True))
        return 0 if registry_result["valid"] else 1
    if args.feature_store_command == "build-reference":
        reference_result = build_reference_outputs(
            args.output_dir, fixture_path=args.fixture, overwrite=args.overwrite
        )
        print(f"output_dir: {reference_result.output_dir}")
        print(f"retrieval_manifest: {reference_result.retrieval_manifest}")
        print(f"validation_report: {reference_result.validation_report}")
        print(f"historical_training_set: {reference_result.historical_training_set}")
        print(f"batch_scoring_set: {reference_result.batch_scoring_set}")
        print(f"checksums: {reference_result.checksums}")
        return 0
    registry = Path("feature_store/registry")
    if args.feature_store_command == "list-entities":
        for entity in yaml.safe_load((registry / "entities.yaml").read_text())["entities"]:
            print(f"{entity['entity_id']}: {entity['canonical_join_key']}")
        return 0
    if args.feature_store_command == "list-features":
        for feature in yaml.safe_load((registry / "features.yaml").read_text())["features"]:
            print(f"{feature['feature_id']}: {feature['feature_name']}")
        return 0
    if args.feature_store_command == "describe-feature":
        for feature in yaml.safe_load((registry / "features.yaml").read_text())["features"]:
            if feature["feature_id"] == args.feature_id:
                print(json.dumps(feature, indent=2, sort_keys=True))
                return 0
        print(f"error: unknown feature {args.feature_id}")
        return 2
    return 2


def _powerbi(args: argparse.Namespace) -> int:
    if args.powerbi_command == "validate-model":
        validation_result = validate_model()
        print(json.dumps(validation_result, indent=2, sort_keys=True))
        return 0 if validation_result["valid"] else 1
    if args.powerbi_command == "generate-reference":
        reference_result = build_powerbi_reference_outputs(
            args.output_dir, overwrite=args.overwrite
        )
        print(f"output_dir: {reference_result.output_dir}")
        print(f"semantic_model_manifest: {reference_result.semantic_model_manifest}")
        print(f"validation_report: {reference_result.validation_report}")
        print(f"checksums: {reference_result.checksums}")
        return 0
    if args.powerbi_command == "verify-reference":
        verification_result = verify_reference_outputs(args.output_dir)
        print(json.dumps(verification_result, indent=2, sort_keys=True))
        return 0 if verification_result["valid"] else 1
    metadata = load_powerbi_metadata()
    model = metadata["model"]
    if args.powerbi_command == "list-tables":
        for table in model["tables"]:
            print(f"{table['table_id']}: {table['display_name']} <- {table['source_model']}")
        return 0
    if args.powerbi_command == "list-measures":
        for measure in model["measures"]:
            print(f"{measure['measure_id']}: {measure['display_name']}")
        return 0
    if args.powerbi_command == "list-kpis":
        for kpi in model["kpis"]:
            print(f"{kpi['kpi_id']}: {kpi['name']} -> {kpi['measure']}")
        return 0
    if args.powerbi_command == "list-reports":
        for report in metadata["reports"]["reports"]:
            print(f"{report['report_id']}: {report['name']}")
        return 0
    if args.powerbi_command == "describe-measure":
        measure = describe_powerbi_measure(args.measure_id)
        if measure is None:
            print(f"error: unknown measure {args.measure_id}")
            return 2
        print(json.dumps(measure, indent=2, sort_keys=True))
        return 0
    return 2


def _governance(args: argparse.Namespace) -> int:
    if args.governance_command == "validate-registry":
        result = validate_governance_registry()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1
    if args.governance_command == "generate-evidence":
        evidence = build_governance_evidence(args.output_dir, overwrite=args.overwrite)
        print(f"output_dir: {evidence.output_dir}")
        print(f"validation_report: {evidence.validation_report}")
        print(f"evidence_manifest: {evidence.evidence_manifest}")
        print(f"checksums: {evidence.checksums}")
        return 0
    if args.governance_command == "verify-evidence":
        result = verify_governance_evidence(args.output_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1
    registry = load_governance_registry()
    if args.governance_command == "list-personas":
        for persona in registry["personas"]["personas"]:
            print(f"{persona['persona_id']}: {persona['export_allowance']}")
        return 0
    if args.governance_command == "list-policies":
        for policy in registry["access"]["policies"]:
            print(f"{policy['policy_id']}: {policy['subject']} {policy['effect']}")
        return 0
    if args.governance_command == "describe-policy":
        policy = describe_governance_policy(args.policy_id)
        if policy is None:
            print(f"error: unknown policy {args.policy_id}")
            return 2
        print(json.dumps(policy, indent=2, sort_keys=True))
        return 0
    if args.governance_command == "evaluate-access":
        decision = evaluate_governance_access(
            persona=args.persona,
            purpose=args.purpose,
            environment=args.environment,
            domain=args.domain,
            object_name=args.object_name,
            operation=args.operation,
            sensitivity=args.sensitivity,
            consent_state=args.consent_state,
            export_request=args.export_request,
        )
        print(json.dumps(decision, indent=2, sort_keys=True))
        return 0 if decision["decision"] == "ALLOW" else 1
    if args.governance_command == "coverage-report":
        result = validate_governance_registry()
        print(json.dumps({k: v for k, v in result.items() if k.endswith("_count")}, indent=2))
        return 0 if result["valid"] else 1
    return 2


def _deployment(args: argparse.Namespace) -> int:
    if args.deployment_command == "validate":
        result = validate_deployment_controls()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1
    if args.deployment_command == "evaluate-policy-gates":
        result = evaluate_policy_gates()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1
    if args.deployment_command == "detect-drift":
        result = detect_drift()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] in {"NO_DRIFT", "DRIFT_DETECTED"} else 1
    if args.deployment_command == "generate-release":
        registry = load_deployment_registry()
        print(json.dumps(registry["release"], indent=2, sort_keys=True))
        return 0
    if args.deployment_command == "generate-manifests":
        registry = load_deployment_registry()
        print(json.dumps(registry["environments"], indent=2, sort_keys=True))
        return 0
    if args.deployment_command == "validate-plan-metadata":
        registry = load_deployment_registry()
        result = {
            "valid": True,
            "required_fields": registry["terraform"]["plan_metadata_required"],
            "apply_jobs_enabled": registry["promotion"]["apply_jobs_enabled"],
            "production_auto_apply": registry["promotion"]["production_auto_apply"],
            "limitations": "Static plan contract only; no Terraform plan was created.",
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.deployment_command == "generate-evidence":
        evidence = build_deployment_evidence(args.output_dir, overwrite=args.overwrite)
        print(f"output_dir: {evidence.output_dir}")
        print(f"validation_report: {evidence.validation_report}")
        print(f"release_manifest: {evidence.release_manifest}")
        print(f"checksums: {evidence.checksums}")
        return 0
    if args.deployment_command == "verify-evidence":
        result = verify_deployment_evidence(args.output_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1
    return 2


def _recovery(args: argparse.Namespace) -> int:
    if args.recovery_command == "validate-registry":
        result = validate_recovery_registry()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1
    if args.recovery_command == "list-tiers":
        registry = load_recovery_registry()
        for tier in registry["recovery_tiers"]:
            print(f"{tier['tier_id']}: RTO {tier['rto_minutes']}m / RPO {tier['rpo_minutes']}m")
        return 0
    if args.recovery_command == "list-scenarios":
        registry = load_recovery_registry()
        for scenario in registry["recovery_scenarios"]:
            print(f"{scenario['scenario_id']}: {scenario['expected_status']}")
        return 0
    if args.recovery_command == "describe-scenario":
        scenario = describe_recovery_scenario(args.scenario_id)
        if scenario is None:
            print(f"error: unknown recovery scenario {args.scenario_id}")
            return 1
        print(json.dumps(scenario, indent=2, sort_keys=True))
        return 0
    if args.recovery_command == "simulate-failover":
        result = simulate_failover(args.scenario_id)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] != "RECOVERY_BLOCKED" else 1
    if args.recovery_command == "validate-recovery":
        result = validate_recovery_registry()
        print(json.dumps({"valid": result["valid"], "errors": result["errors"]}, indent=2))
        return 0 if result["valid"] else 1
    if args.recovery_command == "generate-evidence":
        evidence = build_recovery_evidence(args.output_dir, overwrite=args.overwrite)
        print(f"output_dir: {evidence.output_dir}")
        print(f"validation_report: {evidence.validation_report}")
        print(f"recovery_manifest: {evidence.recovery_manifest}")
        print(f"checksums: {evidence.checksums}")
        return 0
    if args.recovery_command == "verify-evidence":
        result = verify_recovery_evidence(args.output_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1
    return 2


def _operations(args: argparse.Namespace) -> int:
    if args.operations_command == "validate-registry":
        result = validate_operations_registry()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1
    if args.operations_command == "list-services":
        registry = load_operations_registry()
        for service in registry["services"]:
            print(f"{service['service_id']}: {service['recovery_tier']} / {service['criticality']}")
        return 0
    if args.operations_command == "list-slos":
        registry = load_operations_registry()
        for slo in registry["slos"]:
            print(f"{slo['slo_id']}: {slo['target']}% over {slo['window']}")
        return 0
    if args.operations_command == "list-drills":
        registry = load_operations_registry()
        for drill in registry["drills"]:
            print(f"{drill['drill_id']}: {drill['scenario']}")
        return 0
    if args.operations_command == "describe-drill":
        drill = describe_drill(args.drill_id)
        if drill is None:
            print(f"error: unknown operations drill {args.drill_id}")
            return 1
        print(json.dumps(drill, indent=2, sort_keys=True))
        return 0
    if args.operations_command == "evaluate-health":
        result = evaluate_health()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["overall_state"] in {"HEALTHY", "DEGRADED"} else 1
    if args.operations_command == "simulate-incident":
        result = simulate_incident()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.operations_command == "simulate-drill":
        result = simulate_drill()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] != "DRILL_FAILED" else 1
    if args.operations_command == "generate-evidence":
        evidence = build_operations_evidence(args.output_dir, overwrite=args.overwrite)
        print(f"output_dir: {evidence.output_dir}")
        print(f"validation_report: {evidence.validation_report}")
        print(f"health_report: {evidence.health_report}")
        print(f"incident_simulation: {evidence.incident_simulation}")
        print(f"drill_simulation: {evidence.drill_simulation}")
        print(f"checksums: {evidence.checksums}")
        return 0
    if args.operations_command == "verify-evidence":
        result = verify_operations_evidence(args.output_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1
    return 2


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    args = build_parser().parse_args(argv)
    try:
        if args.command == "info":
            return info()
        if args.command == "generate":
            return _generate(args)
        if args.command == "validate-data":
            return _validate_data(args)
        if args.command == "validate-billing":
            return _validate_data(args)
        if args.command == "describe-profile":
            return _describe(args)
        if args.command == "list-datasets":
            return _list_datasets(args)
        if args.command == "describe-schema":
            return _describe_schema(args)
        if args.command == "generate-negative":
            return _generate_negative(args)
        if args.command == "snowflake-validate":
            return _snowflake_validate(args)
        if args.command == "snowflake-inventory":
            return _snowflake_inventory(args)
        if args.command == "snowflake-render":
            return _snowflake_render(args)
        if args.command == "interoperability":
            return _interoperability(args)
        if args.command == "assurance-evidence":
            return _assurance_evidence(args)
        if args.command == "dataiku-reference":
            return _dataiku_reference(args)
        if args.command == "feature-store":
            return _feature_store(args)
        if args.command == "powerbi":
            return _powerbi(args)
        if args.command == "governance":
            return _governance(args)
        if args.command == "deployment":
            return _deployment(args)
        if args.command == "recovery":
            return _recovery(args)
        if args.command == "operations":
            return _operations(args)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}")
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
