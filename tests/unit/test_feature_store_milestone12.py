from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from healthcare_platform.feature_store import build_reference_outputs, validate_registry

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "feature_store" / "registry"
OUTPUTS = ROOT / "feature_store" / "reference" / "outputs"


def _yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return cast(dict[str, Any], loaded)


def test_feature_registry_is_authoritative_and_valid() -> None:
    result = validate_registry(REGISTRY)
    assert result == {
        "valid": True,
        "errors": [],
        "entity_count": 5,
        "feature_count": 8,
        "feature_view_count": 5,
        "feature_set_count": 2,
        "consumer_count": 2,
    }


def test_entities_reuse_canonical_keys_and_owners() -> None:
    entities = _yaml(REGISTRY / "entities.yaml")["entities"]
    keys = {entity["entity_id"]: entity["canonical_join_key"] for entity in entities}
    assert keys["patient"] == "patient_key"
    assert keys["appointment"] == "appointment_key"
    assert keys["payer"] == "payer_key"
    assert keys["billing_exception"] == "reconciliation_exception_key"
    for entity in entities:
        assert entity["upstream_owning_model"]
        assert entity["key_data_type"] == "varchar"
        assert entity["ownership"].isupper()
        assert entity["lifecycle_status"] == "ACTIVE"


def test_features_have_time_semantics_lineage_and_no_leakage() -> None:
    features = _yaml(REGISTRY / "features.yaml")["features"]
    ids = [feature["feature_id"] for feature in features]
    names = [feature["feature_name"] for feature in features]
    assert len(ids) == len(set(ids))
    assert {"priority_score", "priority_band", "material_remediation_required"}.isdisjoint(names)
    for feature in features:
        assert feature["reusable"] is True
        assert feature["source_model"]
        assert feature["source_columns"]
        assert feature["event_time_column"]
        assert feature["availability_time_column"]
        assert "observation_time" in feature["point_in_time_rule"]
        assert feature["freshness_expectation"]
        assert feature["default_value_policy"]
        assert feature["null_policy"]
        assert feature["version"].count(".") == 2
        assert feature["owner"].isupper()


def test_feature_views_and_feature_sets_resolve_membership() -> None:
    features = {feature["feature_id"] for feature in _yaml(REGISTRY / "features.yaml")["features"]}
    views = _yaml(REGISTRY / "feature_views.yaml")["feature_views"]
    sets = _yaml(REGISTRY / "feature_sets.yaml")["feature_sets"]
    view_ids = {view["feature_view_id"] for view in views}
    for view in views:
        assert view["grain"]
        assert view["event_timestamp"]
        assert view["availability_timestamp"]
        assert view["offline_store_contract"].startswith("CURATED.FEATURES.")
        assert set(view["features"]).issubset(features)
    approved = next(
        item
        for item in sets
        if item["feature_set_id"] == "billing_exception_prioritisation_features"
    )
    assert approved["status"] == "APPROVED"
    assert approved["version"] == "1.0.0"
    assert set(approved["feature_views"]).issubset(view_ids)
    assert "material_remediation_required" in approved["excluded_features"]


def test_consumers_and_dataiku_reference_registry_version() -> None:
    consumers = _yaml(REGISTRY / "consumers.yaml")["consumers"]
    dataiku = next(
        item
        for item in consumers
        if item["consumer_id"] == "dataiku_billing_exception_prioritisation"
    )
    assert dataiku["feature_set_id"] == "billing_exception_prioritisation_features"
    assert dataiku["feature_set_version"] == "1.0.0"

    experiment_path = (
        ROOT
        / "dataiku/projects/healthcare_analytics/experiments"
        / "billing_exception_priority_experiment.yaml"
    )
    experiment = _yaml(experiment_path)
    model_registry = _yaml(
        ROOT / "dataiku/projects/healthcare_analytics/models/model_registry.yaml"
    )
    assert experiment["feature_set_id"] == dataiku["feature_set_id"]
    assert experiment["feature_set_version"] == dataiku["feature_set_version"]
    assert model_registry["models"][0]["feature_set_id"] == dataiku["feature_set_id"]


def test_reference_outputs_are_point_in_time_and_checksummed() -> None:
    validation = json.loads((OUTPUTS / "validation_report.json").read_text(encoding="utf-8"))
    assert validation["valid"] is True
    assert validation["point_in_time_valid"] is True
    assert validation["online_serving"] == "deferred"
    for filename in ["historical_training_set.csv", "batch_scoring_set.csv"]:
        with (OUTPUTS / filename).open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows
        keys = {(row["entity_key"], row["observation_timestamp"]) for row in rows}
        assert len(keys) == len(rows)
        for row in rows:
            assert row["feature_set_version"] == "1.0.0"
            assert row["synthetic_flag"] == "true"
            assert row["source_lineage"]
            assert row["retrieval_timestamp"] == "2025-01-01T00:00:00+00:00"
    for line in (OUTPUTS / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(maxsplit=1)
        assert len(digest) == 64
        assert (OUTPUTS / relative).exists()


def test_reference_generation_is_deterministic(tmp_path: Path) -> None:
    first = build_reference_outputs(tmp_path / "first")
    second = build_reference_outputs(tmp_path / "second")
    for name in [
        "entity_registry.json",
        "feature_registry.json",
        "feature_view_registry.json",
        "feature_set_registry.json",
        "historical_training_set.csv",
        "batch_scoring_set.csv",
        "retrieval_manifest.json",
        "validation_report.json",
        "checksums.sha256",
    ]:
        assert (first.output_dir / name).read_text(encoding="utf-8") == (
            second.output_dir / name
        ).read_text(encoding="utf-8")


def test_dbt_feature_models_use_refs_and_no_raw_sources() -> None:
    feature_root = ROOT / "dbt/models/curated/features"
    sql = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in feature_root.glob("**/*.sql")
    )
    assert "{{ ref(" in sql
    assert "{{ source(" not in sql
    for prohibited in [
        "raw_billing",
        "raw_clinical",
        "raw_finance",
        "priority_score",
        "priority_band",
        "material_remediation_required",
        "redis",
        "kafka",
        "feast",
        "power bi",
        "fabric",
    ]:
        assert prohibited not in sql
    assert "current_timestamp()" in sql
    assert "dateadd(day" in sql


def test_lifecycle_quality_and_contracts_are_defined() -> None:
    lifecycle = _yaml(REGISTRY / "lifecycle.yaml")
    quality = _yaml(REGISTRY / "quality.yaml")
    historical = _yaml(ROOT / "feature_store/contracts/historical_retrieval_contract.yaml")
    scoring = _yaml(ROOT / "feature_store/contracts/batch_scoring_retrieval_contract.yaml")
    assert "ACTIVE" in lifecycle["allowed_statuses"]
    assert "DEPRECATED" in lifecycle["allowed_statuses"]
    assert "no_point_in_time_leakage" in {
        item["expectation_id"] for item in quality["quality_expectations"]
    }
    assert historical["feature_set_version"] == "1.0.0"
    assert scoring["online_serving"] == "deferred"


def test_no_online_store_or_later_scope_is_introduced() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in [
            *ROOT.glob("feature_store/**/*"),
            *ROOT.glob("src/healthcare_platform/feature_store/**/*.py"),
        ]
        if path.is_file()
    )
    for prohibited in [
        "redis",
        "dynamodb",
        "cosmos",
        "kafka",
        "online api",
        "power bi artefact",
        "fabric pipeline",
        "production online",
    ]:
        assert prohibited not in text
    assert (
        "online serving is explicitly deferred"
        in (ROOT / "feature_store/README.md").read_text(encoding="utf-8").lower()
    )
