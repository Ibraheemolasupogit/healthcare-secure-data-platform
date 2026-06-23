"""Validated interoperability configuration."""

import json
from pathlib import Path
from typing import Any, cast

DEFAULT_CONFIG_PATH = Path("config/interoperability/foundation.json")


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    required = {
        "schema_version",
        "parser_version",
        "reference_date",
        "source_systems",
        "supported_fhir_resources",
        "supported_hl7_messages",
        "supported_hl7_version",
        "accepted_status_codes",
        "identifier_namespaces",
        "environment",
        "synthetic_flag",
        "warning_threshold",
        "default_output_location",
        "overwrite_default",
    }
    missing = required - config.keys()
    if missing:
        raise ValueError(f"interoperability configuration missing: {sorted(missing)}")
    if config["environment"] not in {"DEV", "TEST", "PROD"}:
        raise ValueError("interoperability environment must be DEV, TEST, or PROD")
    if config["synthetic_flag"] is not True:
        raise ValueError("interoperability processing requires synthetic_flag=true")
    return config
