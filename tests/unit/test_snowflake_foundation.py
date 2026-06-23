import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from healthcare_platform import cli
from healthcare_platform.snowflake_foundation import (
    build_inventory,
    load_foundation,
    render_preview,
    validate_foundation,
    write_inventory,
)


def _write_config(config: dict[str, Any], path: Path) -> Path:
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path


def test_inventory_declares_isolated_environment_objects() -> None:
    config = load_foundation()
    inventory = build_inventory(config)
    assert len(inventory) == 174
    for environment in ("DEV", "TEST", "PROD"):
        objects = [row for row in inventory if row["environment"] == environment]
        assert len(objects) == 58
        assert all(row["object_name"].startswith(f"HEDP_{environment}_") for row in objects)
        assert {row["object_type"] for row in objects} == {
            "ACCOUNT_ROLE",
            "DATABASE",
            "RESOURCE_MONITOR",
            "SCHEMA",
            "TAG",
            "WAREHOUSE",
        }


def test_database_schema_warehouse_and_monitor_contract() -> None:
    config = load_foundation()
    assert set(config["databases"]) == {"RAW", "CURATED", "SERVING", "GOVERNANCE"}
    assert len(config["databases"]["RAW"]["schemas"]) == 8
    assert len(config["databases"]["CURATED"]["schemas"]) == 8
    assert len(config["databases"]["SERVING"]["schemas"]) == 7
    assert len(config["databases"]["GOVERNANCE"]["schemas"]) == 6
    assert set(config["warehouses"]) == {
        "INGEST_WH",
        "TRANSFORM_WH",
        "QUALITY_WH",
        "RESEARCH_WH",
        "BI_WH",
        "ADMIN_WH",
    }
    for warehouse in config["warehouses"].values():
        assert warehouse["resource_monitor"] == "ENVIRONMENT"
        assert warehouse["auto_resume"] is True
        assert warehouse["auto_suspend_seconds"] <= 120


def test_role_grant_and_ownership_contract_is_valid() -> None:
    config = load_foundation()
    declared = set(config["roles"]["ownership"] + config["roles"]["functional"])
    assert "BI_CONSUMER" in declared
    assert "SERVICE_INGEST" in declared
    assert "USER" not in config["ownership_matrix"]["Terraform"]
    assert set(config["ownership_matrix"]) == {
        "Terraform",
        "SQL_VALIDATION",
        "DBT_FUTURE",
        "RUNTIME_FUTURE",
    }
    assert set(config["grants"]["warehouse_usage"]) <= declared
    assert set(config["grants"]["schema_usage"]) <= declared


def test_foundation_and_inventory_validate() -> None:
    result = validate_foundation()
    assert result.valid, result.errors
    assert result.inventory_count == 174
    assert result.warnings == ("Live Snowflake deployment and RBAC probes were not executed.",)


def test_inventory_generation_is_deterministic(tmp_path: Path) -> None:
    config = load_foundation()
    first = write_inventory(config, tmp_path / "first.json")
    second = write_inventory(config, tmp_path / "second.json")
    assert first.read_bytes() == second.read_bytes()


def test_rendering_is_deterministic_and_protects_overwrite(tmp_path: Path) -> None:
    config = load_foundation()
    first = tmp_path / "first"
    second = tmp_path / "second"
    render_preview(config, "DEV", first)
    render_preview(config, "DEV", second)
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
    with pytest.raises(ValueError, match="--overwrite"):
        render_preview(config, "DEV", first)
    with pytest.raises(ValueError, match="environment"):
        render_preview(config, "LOCAL", tmp_path / "invalid")


def test_role_cycle_and_duplicate_role_are_rejected(tmp_path: Path) -> None:
    config = deepcopy(load_foundation())
    config["roles"]["hierarchy"]["DATA_ENGINEER"] = "ANALYTICS_ENGINEER"
    config["roles"]["hierarchy"]["ANALYTICS_ENGINEER"] = "DATA_ENGINEER"
    config["roles"]["functional"].append("DATA_ENGINEER")
    config_path = _write_config(config, tmp_path / "foundation.json")
    inventory_path = write_inventory(config, tmp_path / "inventory.json")
    result = validate_foundation(config_path, inventory_path)
    assert not result.valid
    assert any("cycle" in error for error in result.errors)
    assert any("duplicate declared objects" in error for error in result.errors)


def test_unknown_grant_and_stale_inventory_are_rejected(tmp_path: Path) -> None:
    config = deepcopy(load_foundation())
    config["grants"]["schema_usage"]["BI_CONSUMER"].append("RAW.NOT_A_SCHEMA")
    config_path = _write_config(config, tmp_path / "foundation.json")
    result = validate_foundation(config_path, Path("snowflake/inventory/foundation.json"))
    assert not result.valid
    assert any("unknown references" in error for error in result.errors)
    assert any("inventory configuration hash is stale" in error for error in result.errors)


def _copy_validation_repo(tmp_path: Path) -> Path:
    shutil.copytree("snowflake", tmp_path / "snowflake")
    module = tmp_path / "infrastructure/terraform/modules/snowflake_foundation"
    environment = tmp_path / "infrastructure/terraform/environments/dev"
    module.mkdir(parents=True)
    environment.mkdir(parents=True)
    (module / "main.tf").write_text("# test fixture\n", encoding="utf-8")
    (environment / "main.tf").write_text("# test fixture\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    ("sql", "message"),
    [
        ("drop database forbidden;\n", "destructive SQL keyword"),
        ("grant usage on database x to user person;\n", "direct user grant"),
        ("show databases like 'HEDP_<ENV>_%';\n", "unresolved placeholder"),
    ],
)
def test_unsafe_sql_is_rejected(tmp_path: Path, sql: str, message: str) -> None:
    repo = _copy_validation_repo(tmp_path)
    bad_sql = repo / "snowflake/validation/999_bad.sql"
    bad_sql.write_text(sql, encoding="utf-8")
    result = validate_foundation(
        repo / "snowflake/config/foundation.json",
        repo / "snowflake/inventory/foundation.json",
        repo,
    )
    assert not result.valid
    assert any(message in error for error in result.errors)


def test_snowflake_cli_commands(tmp_path: Path, capsys: Any) -> None:
    inventory = tmp_path / "inventory.json"
    assert cli.main(["snowflake-inventory", "--output", str(inventory)]) == 0
    assert inventory.exists()
    assert cli.main(["snowflake-render", "--output-dir", str(tmp_path / "preview")]) == 0
    assert "100_object_inventory.sql" in capsys.readouterr().out
    assert (
        cli.main(
            [
                "snowflake-validate",
                "--inventory",
                str(inventory),
            ]
        )
        == 0
    )
