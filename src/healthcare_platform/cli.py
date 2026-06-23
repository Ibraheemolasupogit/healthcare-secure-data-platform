"""Foundation command-line interface."""

import argparse
import importlib.util
import json
import platform
from dataclasses import replace
from datetime import date
from pathlib import Path

from healthcare_platform.config import load_settings, snowflake_credentials_present
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
    generate.add_argument("--patient-count", type=int)
    generate.add_argument("--inject-defects", action="store_true")
    generate.add_argument("--negative-test-mode", action="store_true")
    generate.add_argument("--overwrite", action="store_true")
    generate.add_argument("--config", type=Path, default=DEFAULT_PROFILE_PATH)
    validate_parser = subparsers.add_parser("validate-data", help="validate a generated output")
    validate_parser.add_argument("--input-dir", type=Path, required=True)
    describe = subparsers.add_parser(
        "describe-profile", help="show profile configuration and estimates"
    )
    describe.add_argument("profile", choices=("small", "medium", "large"))
    describe.add_argument("--config", type=Path, default=DEFAULT_PROFILE_PATH)
    subparsers.add_parser("list-datasets", help="list canonical datasets and schema versions")
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


def _list_datasets() -> int:
    for name in DATASET_ORDER:
        print(f"{name}: schema {SCHEMAS[name].schema_version} — {SCHEMAS[name].description}")
    return 0


def _validate_data(args: argparse.Namespace) -> int:
    report = validate_directory(args.input_dir)
    report.write(args.input_dir)
    print(f"validation: {'PASS' if report.valid else 'FAIL'}")
    print(f"rows_validated: {report.rows_validated}")
    print(f"issues: {len(report.issues)}")
    return 0 if report.valid else 1


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
        if args.command == "describe-profile":
            return _describe(args)
        if args.command == "list-datasets":
            return _list_datasets()
        if args.command == "snowflake-validate":
            return _snowflake_validate(args)
        if args.command == "snowflake-inventory":
            return _snowflake_inventory(args)
        if args.command == "snowflake-render":
            return _snowflake_render(args)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}")
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
