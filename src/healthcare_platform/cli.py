"""Foundation command-line interface."""

import argparse
import importlib.util
import platform

from healthcare_platform.config import load_settings, snowflake_credentials_present
from healthcare_platform.logging_config import configure_logging

PROJECT_NAME = "Healthcare Secure Data Platform"


def dbt_available() -> bool:
    """Return whether dbt Core is importable in the current environment."""
    return importlib.util.find_spec("dbt") is not None


def build_parser() -> argparse.ArgumentParser:
    """Build the command parser."""
    parser = argparse.ArgumentParser(prog="healthcare-platform")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("info", help="show safe local environment diagnostics")
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


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    args = build_parser().parse_args(argv)
    if args.command == "info":
        return info()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
