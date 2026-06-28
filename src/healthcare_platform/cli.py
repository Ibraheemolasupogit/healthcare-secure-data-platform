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
from healthcare_platform.feature_store import build_reference_outputs, validate_registry
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
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}")
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
