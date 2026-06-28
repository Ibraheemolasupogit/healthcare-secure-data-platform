from __future__ import annotations

# ruff: noqa: E402,I001

import ast
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AIRFLOW_ROOT = ROOT / "orchestration" / "airflow"
INCLUDE_ROOT = AIRFLOW_ROOT / "include"
if str(INCLUDE_ROOT) not in sys.path:
    sys.path.insert(0, str(INCLUDE_ROOT))

from callbacks import failure_record  # type: ignore[import-not-found]  # noqa: E402
from commands import (  # type: ignore[import-not-found]  # noqa: E402
    assurance_evidence_command,
    dbt_build_command,
    generate_sources_command,
    healthcare_platform_command,
)
from configuration import (  # type: ignore[import-not-found]  # noqa: E402
    AirflowPlatformConfig,
    load_config,
    selector_for,
)
from constants import (  # type: ignore[import-not-found]  # noqa: E402
    AIRFLOW_VERSION,
    DBT_SELECTORS,
    SUPPORTED_EXECUTION_MODES,
)
from evidence import (  # type: ignore[import-not-found]  # noqa: E402
    WorkflowRunManifest,
    write_checksums,
    write_task_summary,
    write_workflow_manifest,
)


DAG_FILES = sorted(
    path for path in (AIRFLOW_ROOT / "dags").glob("*.py") if path.name != "_common.py"
)
EXPECTED_DAG_IDS = {
    "healthcare_source_preparation",
    "interoperability_ingestion",
    "healthcare_dbt_pipeline",
    "billing_assurance_pipeline",
    "healthcare_platform_end_to_end",
}


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parsed(path: Path) -> ast.Module:
    return ast.parse(_source(path))


def _literal_strings(node: ast.AST) -> list[str]:
    values: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            values.append(child.value)
    return values


def test_required_dag_files_and_ids_are_present() -> None:
    assert {path.stem for path in DAG_FILES} == EXPECTED_DAG_IDS
    discovered_ids: set[str] = set()
    for path in DAG_FILES:
        strings = _literal_strings(_parsed(path))
        discovered_ids.update(value for value in strings if value in EXPECTED_DAG_IDS)
        assert "create_dag(" in _source(path)
    assert discovered_ids == EXPECTED_DAG_IDS


def test_dag_schedules_catchup_start_date_and_limits_are_explicit() -> None:
    common = _source(AIRFLOW_ROOT / "dags" / "_common.py")
    assert "DEFAULT_START_DATE" in common
    assert "catchup=CONFIG.catchup" in common
    assert "max_active_runs=CONFIG.max_active_runs" in common
    assert "datetime.now(" not in common
    assert "retries" in common
    assert "execution_timeout" in common
    assert "on_failure_callback" in common
    for path in DAG_FILES:
        source = _source(path)
        assert "schedule=" in source
        assert "datetime.now(" not in source


def test_workflow_dependency_order_is_encoded() -> None:
    dbt_pipeline = _source(AIRFLOW_ROOT / "dags" / "healthcare_dbt_pipeline.py")
    assert "dbt_preflight >> source_freshness >> staging >> healthcare_core" in dbt_pipeline
    assert "healthcare_core >> billing_finance >> assurance" in dbt_pipeline
    assert "assurance >> dbt_tests >> docs_metadata" in dbt_pipeline

    end_to_end = _source(AIRFLOW_ROOT / "dags" / "healthcare_platform_end_to_end.py")
    assert "source_preparation" in end_to_end
    assert "interoperability_ingestion" in end_to_end
    assert "dbt_staging" in end_to_end
    assert "dbt_core" in end_to_end
    assert "dbt_billing_finance" in end_to_end
    assert "dbt_assurance" in end_to_end
    assert "assurance_evidence" in end_to_end


def test_airflow_boundary_does_not_duplicate_business_logic_or_later_milestones() -> None:
    text = "\n".join(_source(path).lower() for path in [*DAG_FILES, *INCLUDE_ROOT.glob("*.py")])
    prohibited = [
        "select ",
        "insert ",
        "update ",
        "merge ",
        "tariff_match_status",
        "contract_match_status",
        "allocation_status",
        "financial_value_at_risk",
        "dataiku",
        "power bi",
        "fabric",
        "feature_store",
        "pagerduty",
        "slack",
        "teams",
    ]
    for term in prohibited:
        assert term not in text
    assert "healthcare-platform" in text
    assert "dbt" in text


def test_configuration_defaults_are_safe_and_authoritative(monkeypatch: Any) -> None:
    monkeypatch.delenv("HEALTHCARE_AIRFLOW_CONNECTED_SNOWFLAKE", raising=False)
    monkeypatch.delenv("HEALTHCARE_AIRFLOW_EXECUTION_MODE", raising=False)
    config = load_config()

    assert SUPPORTED_EXECUTION_MODES == ("fixture", "local_generation", "connected_snowflake")
    assert config.execution_mode == "fixture"
    assert config.connected_snowflake_enabled is False
    assert config.allow_large_generation is False
    assert config.overwrite_outputs is False
    assert config.notification_integrations_enabled is False
    assert config.retry_count == 1
    assert config.catchup is False
    assert config.max_active_runs == 1
    assert config.validate() == []


def test_unsafe_configuration_is_rejected() -> None:
    config = AirflowPlatformConfig(
        environment="local",
        execution_mode="connected_snowflake",
        repository_root=ROOT,
        output_root=ROOT / "outputs/orchestration",
        profile="large",
        seed=42,
        reference_date=__import__("datetime").date(2025, 1, 1),
        source_data_path=ROOT / "data/samples/small",
        interoperability_path=ROOT / "data/samples/interoperability",
        assurance_evidence_output=ROOT / "outputs/orchestration/assurance",
        dbt_project_dir=ROOT / "dbt",
        dbt_profiles_dir=ROOT / "dbt",
        dbt_target="dev",
        connected_snowflake_enabled=False,
        allow_large_generation=False,
        overwrite_outputs=False,
        retry_count=10,
        retry_delay_seconds=60,
        execution_timeout_minutes=0,
        sensor_timeout_seconds=0,
        sensor_poke_interval_seconds=5,
        catchup=False,
        max_active_runs=0,
        notification_integrations_enabled=True,
    )
    errors = "\n".join(config.validate())
    assert "explicit enablement" in errors
    assert "large generation is disabled" in errors
    assert "retry count" in errors
    assert "external notifications" in errors


def test_command_construction_is_shell_safe_and_reuses_existing_contracts() -> None:
    config = load_config()
    command = generate_sources_command(config, ROOT / "outputs/orchestration/demo")
    assert command.startswith("healthcare-platform generate")
    assert "--seed 42" in command
    assert "--reference-date 2025-01-01" in command
    assert "--overwrite" not in command

    quoted = healthcare_platform_command("validate-data", "--input-dir", "path with spaces")
    assert "'path with spaces'" in quoted
    assert "SNOWFLAKE_PASSWORD" not in quoted
    assert selector_for("assurance") == "tag:assurance"
    assert DBT_SELECTORS == {
        "staging": "path:models/staging",
        "core": "tag:core",
        "billing": "tag:billing",
        "finance": "tag:finance",
        "assurance": "tag:assurance",
    }
    assert "dbt build --select tag:billing" in dbt_build_command(config, "billing")
    assert assurance_evidence_command(ROOT / "outputs/orchestration/assurance").startswith(
        "healthcare-platform assurance-evidence"
    )


def test_failure_callback_and_manifest_exclude_sensitive_payloads(tmp_path: Path) -> None:
    record = failure_record(
        {
            "dag_id": "demo",
            "task_id": "task",
            "run_id": "run",
            "logical_date": "2025-01-01",
            "exception": ValueError("boom"),
            "params": {"batch_id": "batch"},
        },
        tmp_path,
        "fixture",
    )
    assert record["synthetic_flag"] is True
    text = (tmp_path / "failure_events.jsonl").read_text(encoding="utf-8")
    assert "SNOWFLAKE" not in text
    assert "patient" not in text.lower()

    manifest_path = write_workflow_manifest(
        tmp_path,
        WorkflowRunManifest(
            workflow_run_id="demo-2025-01-01",
            dag_id="demo",
            logical_date="2025-01-01",
            data_interval_start="2025-01-01",
            data_interval_end="2025-01-02",
            execution_mode="fixture",
            environment="local",
            source_profile="small",
            seed=42,
            reference_date="2025-01-01",
            task_count=3,
            successful_task_count=3,
            skipped_task_count=0,
            failed_task_count=0,
            connected_execution_status="disabled",
            synthetic_flag=True,
            limitations=["not scheduler-produced", "not Snowflake-connected"],
        ),
    )
    summary_path = write_task_summary(
        tmp_path,
        [
            {
                "dag_id": "demo",
                "task_id": "task",
                "status": "success",
                "contract": "cli",
                "execution_mode": "fixture",
            }
        ],
    )
    checksums_path = write_checksums(tmp_path, [manifest_path, summary_path])
    assert json.loads(manifest_path.read_text())["execution_mode"] == "fixture"
    assert checksums_path.read_text(encoding="utf-8")


def test_dependency_strategy_and_airflow_version_are_separate() -> None:
    requirements = (ROOT / "requirements-airflow.txt").read_text(encoding="utf-8")
    assert f"apache-airflow=={AIRFLOW_VERSION}" in requirements
    assert "constraints-" in requirements
    assert "apache-airflow" not in (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
