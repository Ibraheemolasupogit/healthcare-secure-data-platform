"""Snowflake foundation source contract and deterministic local tooling."""

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

DEFAULT_CONFIG_PATH = Path("snowflake/config/foundation.json")
DEFAULT_INVENTORY_PATH = Path("snowflake/inventory/foundation.json")
DEFAULT_ORDER_PATH = Path("snowflake/deployment/order.json")
SUPPORTED_ENVIRONMENTS = ("DEV", "TEST", "PROD")
NAME_PATTERN = re.compile(r"^HEDP_(DEV|TEST|PROD)_[A-Z][A-Z0-9_]*$")
FORBIDDEN_SQL = re.compile(r"\b(DROP|TRUNCATE|UNDROP)\b", re.IGNORECASE)
UNRESOLVED_TOKEN = re.compile(r"(\{\{|\}\}|<ENV>|<ACCOUNT|<ORG|<REGION)", re.IGNORECASE)


@dataclass(frozen=True)
class FoundationValidation:
    """Static validation result that never contacts Snowflake."""

    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    inventory_count: int
    configuration_sha256: str


def load_foundation(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load the single JSON contract shared by Python and Terraform."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def configuration_sha256(config: dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def object_name(config: dict[str, Any], environment: str, suffix: str) -> str:
    return f"{config['name_prefix']}_{environment}_{suffix}"


def build_inventory(config: dict[str, Any]) -> list[dict[str, str]]:
    """Build stable declared-object inventory for all supported environments."""
    rows: list[dict[str, str]] = []

    def add(
        environment: str,
        object_type: str,
        name: str,
        owner: str,
        purpose: str,
        classification: str,
        database: str = "",
        schema: str = "",
    ) -> None:
        rows.append(
            {
                "environment": environment,
                "object_type": object_type,
                "object_name": name,
                "database_name": database,
                "schema_name": schema,
                "owner_role": owner,
                "functional_purpose": purpose,
                "deployment_owner": "Terraform",
                "data_classification": classification,
                "milestone": "3",
                "status": config["status"],
            }
        )

    role_suffixes = config["roles"]["ownership"] + config["roles"]["functional"]
    for environment in config["supported_environments"]:
        for database_key, database in config["databases"].items():
            database_name = object_name(config, environment, database_key)
            owner = object_name(config, environment, database["owner_role"])
            add(
                environment,
                "DATABASE",
                database_name,
                owner,
                database["purpose"],
                database["classification"],
                database_name,
            )
            for schema_name, purpose in database["schemas"].items():
                add(
                    environment,
                    "SCHEMA",
                    f"{database_name}.{schema_name}",
                    owner,
                    purpose,
                    database["classification"],
                    database_name,
                    schema_name,
                )
        for monitor_key, monitor in config["resource_monitors"].items():
            add(
                environment,
                "RESOURCE_MONITOR",
                object_name(config, environment, f"RM_{monitor_key}"),
                object_name(config, environment, monitor["owner_role"]),
                monitor["purpose"],
                "OPERATIONAL",
            )
        for warehouse_key, warehouse in config["warehouses"].items():
            add(
                environment,
                "WAREHOUSE",
                object_name(config, environment, warehouse_key),
                object_name(config, environment, warehouse["owner_role"]),
                warehouse["purpose"],
                "OPERATIONAL",
            )
        for role_suffix in role_suffixes:
            role_type = "OWNERSHIP" if role_suffix in config["roles"]["ownership"] else "FUNCTIONAL"
            add(
                environment,
                "ACCOUNT_ROLE",
                object_name(config, environment, role_suffix),
                "SECURITYADMIN",
                f"{role_type.title()} role for {role_suffix.lower().replace('_', ' ')}.",
                "GOVERNANCE",
            )
        for tag_name, tag in config["tags"].items():
            database_name = object_name(config, environment, tag["database"])
            add(
                environment,
                "TAG",
                f"{database_name}.{tag['schema']}.{tag_name}",
                object_name(config, environment, tag["owner_role"]),
                tag["purpose"],
                "GOVERNANCE",
                database_name,
                tag["schema"],
            )
    return sorted(
        rows, key=lambda row: (row["environment"], row["object_type"], row["object_name"])
    )


def write_inventory(config: dict[str, Any], path: Path = DEFAULT_INVENTORY_PATH) -> Path:
    """Write deterministic machine-readable inventory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0.0",
        "configuration_sha256": configuration_sha256(config),
        "objects": build_inventory(config),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _role_cycle(config: dict[str, Any], environment: str) -> str | None:
    hierarchy = config["roles"]["hierarchy"]
    external = set(config["roles"]["external_parents"])
    for start in hierarchy:
        seen: set[str] = set()
        current = start
        while current not in external and current in hierarchy:
            if current in seen:
                return f"{environment} role hierarchy cycle includes {current}"
            seen.add(current)
            current = hierarchy[current]
    return None


def _validate_sql(repo_root: Path, errors: list[str]) -> None:
    for path in sorted((repo_root / "snowflake").rglob("*.sql")):
        relative = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8")
        if FORBIDDEN_SQL.search(text):
            errors.append(f"destructive SQL keyword in {relative}")
        if UNRESOLVED_TOKEN.search(text):
            errors.append(f"unresolved placeholder in {relative}")
        if re.search(r"\bGRANT\s+[^;]+\s+TO\s+USER\b", text, re.IGNORECASE):
            errors.append(f"direct user grant in {relative}")
    for path in sorted((repo_root / "infrastructure" / "terraform").rglob("*.tf")):
        relative = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8")
        if re.search(r'resource\s+"snowflake_user"', text):
            errors.append(f"user resource is outside Milestone 3 scope in {relative}")
        if re.search(r"\buser_name\s*=", text):
            errors.append(f"direct user role grant is forbidden in {relative}")


def validate_foundation(
    config_path: Path = DEFAULT_CONFIG_PATH,
    inventory_path: Path = DEFAULT_INVENTORY_PATH,
    repo_root: Path = Path("."),
) -> FoundationValidation:
    """Validate names, relationships, isolation, inventory and safe SQL statically."""
    config = load_foundation(config_path)
    errors: list[str] = []
    warnings: list[str] = ["Live Snowflake deployment and RBAC probes were not executed."]
    if tuple(config.get("supported_environments", ())) != SUPPORTED_ENVIRONMENTS:
        errors.append("supported_environments must be DEV, TEST, PROD in that order")
    if config.get("name_prefix") != "HEDP":
        errors.append("name_prefix must be HEDP")
    forbidden_keys = {
        "account_locator",
        "account_name",
        "organization_name",
        "region",
        "user",
        "password",
    }
    if forbidden_keys.intersection(config):
        errors.append("account-specific or credential keys are forbidden in foundation config")
    declared_roles = set(config["roles"]["ownership"] + config["roles"]["functional"])
    external_roles = set(config["roles"]["external_parents"])
    database_keys = set(config["databases"])
    schema_refs = {
        f"{database}.{schema}"
        for database, definition in config["databases"].items()
        for schema in definition["schemas"]
    }
    for environment in SUPPORTED_ENVIRONMENTS:
        for database_key, database in config["databases"].items():
            name = object_name(config, environment, database_key)
            if not NAME_PATTERN.fullmatch(name):
                errors.append(f"invalid database name {name}")
            if environment not in database["retention_days"]:
                errors.append(f"{database_key} has no {environment} retention setting")
        for warehouse_key, warehouse in config["warehouses"].items():
            name = object_name(config, environment, warehouse_key)
            if not NAME_PATTERN.fullmatch(name):
                errors.append(f"invalid warehouse name {name}")
            if environment not in warehouse["sizes"]:
                errors.append(f"{warehouse_key} has no {environment} size")
            if warehouse["resource_monitor"] not in config["resource_monitors"]:
                errors.append(f"{warehouse_key} references an undeclared resource monitor")
            if not set(warehouse["future_consumers"]) <= declared_roles:
                errors.append(f"{warehouse_key} references an undeclared future consumer")
        cycle = _role_cycle(config, environment)
        if cycle:
            errors.append(cycle)
    for child, parent in config["roles"]["hierarchy"].items():
        if child not in declared_roles:
            errors.append(f"role hierarchy child is undeclared: {child}")
        if parent not in declared_roles | external_roles:
            errors.append(f"role hierarchy parent is undeclared: {parent}")
    for grant_group in ("warehouse_usage", "schema_usage", "schema_create", "future_read"):
        for role, references in config["grants"][grant_group].items():
            if role not in declared_roles:
                errors.append(f"{grant_group} references undeclared role {role}")
            valid = set(config["warehouses"]) if grant_group == "warehouse_usage" else schema_refs
            unknown = set(references) - valid
            if unknown:
                errors.append(f"{grant_group} contains unknown references: {sorted(unknown)}")
    for tag in config["tags"].values():
        if tag["database"] not in database_keys:
            errors.append("tag references an undeclared database")
        if f"{tag['database']}.{tag['schema']}" not in schema_refs:
            errors.append("tag references an undeclared schema")
    expected = build_inventory(config)
    names = [(row["environment"], row["object_type"], row["object_name"]) for row in expected]
    if len(names) != len(set(names)):
        errors.append("duplicate declared objects exist")
    if inventory_path.exists():
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        if inventory.get("configuration_sha256") != configuration_sha256(config):
            errors.append("inventory configuration hash is stale")
        if inventory.get("objects") != expected:
            errors.append("inventory does not match declared objects")
    else:
        errors.append(f"inventory is missing: {inventory_path}")
    order_path = repo_root / DEFAULT_ORDER_PATH
    if not order_path.exists():
        errors.append(f"deployment order is missing: {order_path}")
    else:
        order = json.loads(order_path.read_text(encoding="utf-8"))["steps"]
        positions = [step["order"] for step in order]
        if positions != sorted(positions) or len(positions) != len(set(positions)):
            errors.append("deployment ordering is not unique and ascending")
        for step in order:
            if not (repo_root / step["path"]).exists():
                errors.append(f"deployment step path is missing: {step['path']}")
    _validate_sql(repo_root, errors)
    raw = json.dumps(config, sort_keys=True)
    if re.search(r"HEDP_(DEV|TEST|PROD)_.*HEDP_(DEV|TEST|PROD)_", raw):
        warnings.append("Review explicit cross-environment references if introduced later.")
    return FoundationValidation(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        inventory_count=len(expected),
        configuration_sha256=configuration_sha256(config),
    )


def render_preview(
    config: dict[str, Any], environment: str, output_dir: Path, overwrite: bool = False
) -> tuple[Path, ...]:
    """Render deterministic, non-deploying SQL evidence for one environment."""
    environment = environment.upper()
    if environment not in SUPPORTED_ENVIRONMENTS:
        raise ValueError("environment must be DEV, TEST, or PROD")
    if output_dir.exists() and any(output_dir.iterdir()):
        if not overwrite:
            raise ValueError(f"output directory is not empty: {output_dir}; pass --overwrite")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{config['name_prefix']}_{environment}"
    inventory_sql = output_dir / "100_object_inventory.sql"
    inventory_sql.write_text(
        "\n".join(
            [
                "-- LOCALLY RENDERED VALIDATION ONLY; THIS FILE DOES NOT DEPLOY OBJECTS.",
                f"SHOW DATABASES LIKE '{prefix}_%';",
                f"SHOW WAREHOUSES LIKE '{prefix}_%';",
                f"SHOW RESOURCE MONITORS LIKE '{prefix}_%';",
                f"SHOW ROLES LIKE '{prefix}_%';",
                "",
            ]
        ),
        encoding="utf-8",
    )
    grants_sql = output_dir / "110_grants_and_hierarchy.sql"
    role_queries = [
        f"SHOW GRANTS TO ROLE {object_name(config, environment, role)};"
        for role in config["roles"]["ownership"] + config["roles"]["functional"]
    ]
    grants_sql.write_text(
        "\n".join(
            ["-- LOCALLY RENDERED GRANT INSPECTION; REVIEW RESULTS AGAINST RBAC EXPECTATIONS."]
            + role_queries
            + [""]
        ),
        encoding="utf-8",
    )
    expectations = output_dir / "120_rbac_expectations.json"
    expectations.write_text(
        json.dumps(config["rbac_expectations"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    preview_inventory = output_dir / "foundation_inventory.json"
    preview_inventory.write_text(
        json.dumps(
            [row for row in build_inventory(config) if row["environment"] == environment],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return inventory_sql, grants_sql, expectations, preview_inventory
