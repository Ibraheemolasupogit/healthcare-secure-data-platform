from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from healthcare_platform.dataiku import run_reference_pipeline

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "dataiku/projects/healthcare_analytics"


def _yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return cast(dict[str, Any], loaded)


def test_project_blueprint_is_versioned_and_synthetic_only() -> None:
    project = _yaml(PROJECT / "project.yaml")
    assert project["project_key"] == "HEDP_GOVERNED_ANALYTICS"
    assert project["use_case"] == "billing_exception_prioritisation"
    assert project["synthetic_only"] is True
    assert project["deployment_status"] == "not_deployed"
    assert project["snowflake_connection_placeholder"] == "snowflake_healthcare"
    assert "milestone_11" in project["tags"]


def test_flow_graph_is_acyclic_and_uses_trusted_inputs() -> None:
    flow = _yaml(PROJECT / "flow.yaml")
    nodes = {node["id"] for node in flow["nodes"]}
    assert len(nodes) == len(flow["nodes"])
    for source, target in flow["edges"]:
        assert source in nodes
        assert target in nodes
    visited: set[str] = set()
    visiting: set[str] = set()
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for source, target in flow["edges"]:
        adjacency[source].append(target)

    def visit(node: str) -> None:
        assert node not in visiting, "cycle detected"
        if node in visited:
            return
        visiting.add(node)
        for child in adjacency[node]:
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for node in nodes:
        visit(node)
    assert "raw_billing" in flow["prohibited_inputs"]


def test_trusted_inputs_are_governed_dbt_outputs_only() -> None:
    trusted = _yaml(PROJECT / "datasets/trusted_inputs.yaml")
    allowed_models = {
        "reconciliation_exception",
        "exception_remediation_status",
        "revenue_at_risk_summary",
        "billing_exception",
    }
    assert {item["dbt_model"] for item in trusted["trusted_inputs"]} == allowed_models
    blocked = "\n".join(trusted["blocked_inputs"]).lower()
    for prohibited in ("raw_billing", "raw_finance", "raw_clinical", "raw_interoperability"):
        assert prohibited in blocked


def test_analytical_contract_and_features_define_leakage_controls() -> None:
    contract = _yaml(PROJECT / "datasets/analytical_contract.yaml")
    features = _yaml(PROJECT / "features/billing_exception_features.yaml")
    leakage = _yaml(PROJECT / "governance/leakage_controls.yaml")

    assert contract["grain"].startswith("one open governed")
    assert contract["entity_key"] == "reconciliation_exception_key"
    assert contract["label"] == "material_remediation_required"
    assert contract["point_in_time_rule"]
    feature_names = [feature["name"] for feature in features["features"]]
    assert len(feature_names) == len(set(feature_names))
    for feature in features["features"]:
        assert feature["source_model"]
        assert feature["data_type"]
        assert feature["missing_value_handling"] is not None
        assert feature["point_in_time_rule"]
        assert feature["leakage_status"] == "allowed"
    for prohibited in leakage["prohibited_feature_names"]:
        assert prohibited not in feature_names
        assert prohibited in contract["excluded_leakage_columns"]


def test_experiment_models_are_bounded_and_interpretable() -> None:
    experiment = _yaml(PROJECT / "experiments/billing_exception_priority_experiment.yaml")
    assert experiment["target"] == "material_remediation_required"
    assert experiment["random_seed"] == 42
    assert experiment["split_strategy"]["type"] == "temporal"
    assert len(experiment["candidate_models"]) == 2
    assert "deep_learning" in experiment["excluded_models"]
    assert experiment["primary_metric"] == "f1"
    assert experiment["decision_threshold"] == 0.50


def test_scenarios_preserve_airflow_boundary_and_disable_connected_execution() -> None:
    for path in (PROJECT / "scenarios").glob("*.yaml"):
        scenario = _yaml(path)
        assert scenario["status"] == "blueprint_not_scheduled"
        assert scenario["failure_behaviour"]
        text = path.read_text(encoding="utf-8").lower()
        assert "airflow" in text or path.name == "monitoring_scenario.yaml"
        assert "external_notifications: disabled" in text or "external_notifications" not in text


def test_prediction_output_contract_is_governed_and_identifier_safe() -> None:
    contract = _yaml(PROJECT / "deployment/prediction_output_contract.yaml")
    assert (
        contract["snowflake_target"] == "SERVING.ML_OUTPUTS.BILLING_EXCEPTION_PRIORITY_PREDICTIONS"
    )
    assert contract["status"] == "contract_only_not_deployed"
    assert "patient_id" in contract["prohibited_columns"]
    probability = next(
        column for column in contract["columns"] if column["name"] == "predicted_probability"
    )
    assert probability["valid_range"] == [0, 1]


def test_reference_outputs_are_valid_and_checksummed() -> None:
    outputs = PROJECT / "reference_outputs"
    candidate = json.loads((outputs / "candidate_metrics.json").read_text(encoding="utf-8"))
    baseline = json.loads((outputs / "baseline_metrics.json").read_text(encoding="utf-8"))
    selected = json.loads((outputs / "selected_model.json").read_text(encoding="utf-8"))
    assert 0 <= candidate["precision"] <= 1
    assert 0 <= candidate["recall"] <= 1
    assert 0 <= candidate["f1"] <= 1
    assert sum(candidate["confusion_matrix"].values()) == candidate["row_count"]
    assert selected["selected_model"] in {"baseline", "candidate"}
    assert baseline["row_count"] == candidate["row_count"]
    with (outputs / "prediction_sample.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    for row in rows:
        assert row["entity_key"].startswith("EXC-")
        assert 0 <= float(row["predicted_probability"]) <= 1
        assert row["synthetic_flag"] == "true"
    for line in (outputs / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(maxsplit=1)
        assert len(digest) == 64
        assert (outputs / relative).exists()


def test_reference_pipeline_regenerates_deterministically(tmp_path: Path) -> None:
    fixture = PROJECT / "reference_data/billing_exception_analytical_fixture.csv"
    first = run_reference_pipeline(fixture, tmp_path / "first")
    second = run_reference_pipeline(fixture, tmp_path / "second")
    for name in [
        "baseline_metrics.json",
        "candidate_metrics.json",
        "selected_model.json",
        "prediction_sample.csv",
        "model_card.md",
        "checksums.sha256",
    ]:
        assert (first.output_dir / name).read_text(encoding="utf-8") == (
            second.output_dir / name
        ).read_text(encoding="utf-8")


def test_model_card_registry_monitoring_and_approval_are_complete() -> None:
    card = (PROJECT / "models/model_card.md").read_text(encoding="utf-8").lower()
    for section in [
        "intended use",
        "prohibited use",
        "data lineage",
        "target",
        "metrics",
        "subgroup assessment",
        "human oversight",
        "synthetic-data statement",
    ]:
        assert section in card
    registry = _yaml(PROJECT / "models/model_registry.yaml")
    assert registry["registry_status"] == "repository_blueprint_not_dataiku_registry"
    approval = _yaml(PROJECT / "governance/approval_gates.yaml")
    assert approval["approval_status"] == "not_approved_reference_only"
    monitoring = _yaml(PROJECT / "monitoring/model_monitoring.yaml")
    assert monitoring["automatic_retraining"] is False
    assert monitoring["human_review_required"] is True


def test_no_future_scope_or_live_dataiku_credentials_are_introduced() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in PROJECT.glob("**/*")
        if path.is_file()
    )
    for prohibited in [
        "api_key",
        "password",
        "secret",
        "dataikuapi.dssclient",
        "power bi",
        "fabric pipeline",
        "online prediction service",
    ]:
        assert prohibited not in text
    assert "autonomous clinical decisions" in text
    assert "feature store implementation" not in text
