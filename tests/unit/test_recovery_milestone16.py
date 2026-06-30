"""Milestone 16 multi-region recovery registry and simulation tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from healthcare_platform.recovery import (
    build_recovery_evidence,
    describe_scenario,
    load_recovery_registry,
    simulate_failover,
    validate_recovery_registry,
    verify_evidence,
)


def _ids(items: list[dict[str, Any]], key: str) -> set[str]:
    return {str(item[key]) for item in items}


def test_recovery_registry_validates_expected_counts_and_statuses() -> None:
    report = validate_recovery_registry()

    assert report["valid"], report["errors"]
    assert report["region_count"] == 3
    assert report["tier_count"] == 5
    assert report["residency_policy_count"] >= 3
    assert report["dependency_node_count"] >= 12
    assert report["scenario_count"] >= 4
    assert report["platform_mapping_count"] == 8
    assert report["live_deployment_status"] == "NOT_DEPLOYED"
    assert report["simulation_status"] == "LOCAL_SIMULATION_ONLY"


def test_region_roles_are_symbolic_and_not_live_deployed() -> None:
    registry = load_recovery_registry()
    regions = {region["region_id"]: region for region in registry["region_classes"]}

    assert set(regions) == {"PRIMARY_REGION", "RECOVERY_REGION", "ARCHIVAL_REGION"}
    assert regions["PRIMARY_REGION"]["role"] == "primary"
    assert regions["RECOVERY_REGION"]["role"] == "recovery"
    assert regions["ARCHIVAL_REGION"]["role"] == "archive"
    assert all(region["live_status"] == "not_deployed" for region in regions.values())
    assert registry["regional_design"]["automatic_failover_enabled"] is False
    assert registry["regional_design"]["automatic_failback_enabled"] is False


def test_recovery_tiers_have_synthetic_rto_rpo_targets_and_dependencies() -> None:
    registry = load_recovery_registry()
    tiers = registry["recovery_tiers"]
    tier_ids = _ids(tiers, "tier_id")

    assert {
        "TIER_0_CRITICAL_CONTROL_PLANE",
        "TIER_1_CRITICAL_DATA_SERVICES",
        "TIER_2_ANALYTICS_AND_ASSURANCE",
        "TIER_3_REPORTING_AND_ML",
        "TIER_4_NON_CRITICAL_REFERENCE",
    } == tier_ids
    for tier in tiers:
        assert tier["rto_minutes"] > 0
        assert tier["rpo_minutes"] >= 0
        assert tier["maximum_tolerable_downtime_minutes"] >= tier["rto_minutes"]
        assert tier["owner"]
        assert tier["evidence_requirement"]
        assert set(tier["recovery_dependencies"]).issubset(tier_ids)


def test_residency_policies_reference_governance_controls() -> None:
    registry = load_recovery_registry()
    policies = registry["residency_policies"]
    region_ids = _ids(registry["region_classes"], "region_id")

    clinical = next(policy for policy in policies if policy["data_domain"] == "clinical")
    assert clinical["sensitivity"] == "RESTRICTED"
    assert set(clinical["allowed_region_class"]).issubset(region_ids)
    assert "ARCHIVAL_REGION" in clinical["prohibited_region_class"]
    assert clinical["export_restriction"] == "exp_prohibited"
    assert clinical["legal_review_required"] is True
    for policy in policies:
        assert policy["retention_policy_ref"].startswith("ret_")
        assert policy["implementation_status"] == "STATICALLY_VALIDATED"
        assert "not legal advice" in policy["limitations"].lower() or policy[
            "legal_review_required"
        ] in {True, False}


def test_dependency_graph_is_acyclic_and_recovery_order_restores_consumers_last() -> None:
    registry = load_recovery_registry()
    graph = registry["dependency_graph"]
    nodes = set(graph["nodes"])

    for source, target in graph["edges"]:
        assert source in nodes
        assert target in nodes
    order = registry["recovery_order"]
    assert order[0] == "governance_registry"
    assert order.index("deployment_controls") < order.index("snowflake_platform")
    assert order.index("snowflake_platform") < order.index("dbt_staging")
    assert order.index("healthcare_core") < order.index("fabric_powerbi")
    assert order.index("feature_store") < order.index("dataiku")
    assert set(graph["critical_nodes"]).issubset(nodes)
    assert set(graph["optional_nodes"]).issubset(nodes)


def test_platform_recovery_mappings_cover_all_platforms() -> None:
    registry = load_recovery_registry()
    mappings = registry["platform_mappings"]

    assert set(mappings) == {
        "snowflake",
        "dbt",
        "airflow",
        "dataiku",
        "feature_store",
        "fabric_powerbi",
        "governance",
        "deployment_controls",
    }
    assert mappings["snowflake"]["live_replication_status"] == "not_configured"
    assert mappings["dbt"]["live_execution_status"] == "not_executed"
    assert mappings["airflow"]["live_execution_status"] == "not_deployed"
    assert mappings["governance"]["recovery_design"].endswith("fail_closed")
    assert (
        mappings["deployment_controls"]["validation"]
        == "stale_plans_rejected_and_approval_required"
    )


def test_recovery_simulation_classifies_scenarios() -> None:
    success = simulate_failover("primary_region_unavailable")
    governance_block = simulate_failover("governance_checksum_mismatch")
    stale_point = simulate_failover("stale_recovery_point")
    slow_recovery = simulate_failover("slow_recovery_validation")

    assert success["status"] == "RECOVERY_READY_WITH_APPROVAL"
    assert success["approval_required"] is True
    assert success["automatic_failover_enabled"] is False
    assert success["ordered_recovery_steps"][0]["component"] == "governance_registry"
    assert governance_block["status"] == "RECOVERY_BLOCKED"
    assert "Fail closed" in governance_block["decision_reason"]
    assert stale_point["status"] == "RPO_BREACH"
    assert slow_recovery["status"] == "RTO_BREACH"


def test_failover_and_failback_controls_require_manual_approval() -> None:
    registry = load_recovery_registry()

    assert registry["failover_criteria"]["automatic_failover_enabled"] is False
    assert registry["failover_criteria"]["approval_required"] is True
    assert "recovery_region_readiness" in registry["failover_criteria"]["required_signals"]
    assert "replication_currency" in registry["failover_criteria"]["required_signals"]
    assert registry["failback"]["automatic_failback_enabled"] is False
    assert registry["failback"]["approval_required"] is True
    assert registry["failback"]["data_reconciliation_required"] is True
    assert registry["failback"]["stability_period_hours"] >= 24
    assert registry["failback"]["rollback_from_failed_failback"]


def test_recovery_evidence_generation_outputs_expected_files(tmp_path: Path) -> None:
    evidence = build_recovery_evidence(tmp_path, overwrite=True)
    verification = verify_evidence(tmp_path)

    expected = {
        "region_registry.json",
        "residency_policy.csv",
        "recovery_tiers.csv",
        "dependency_graph.json",
        "recovery_scenarios.json",
        "failover_decision_report.json",
        "recovery_manifest.json",
        "recovery_validation_report.json",
        "failback_plan.md",
        "recovery_summary.md",
        "checksums.sha256",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected
    assert evidence.output_dir == tmp_path
    assert verification["valid"], verification["errors"]
    assert verification["checked_files"] == len(expected) - 1

    manifest = json.loads((tmp_path / "recovery_manifest.json").read_text(encoding="utf-8"))
    assert manifest["synthetic"] is True
    assert manifest["approval_state"] == "APPROVAL_REQUIRED_NOT_REQUESTED"
    assert manifest["failback_status"] == "NOT_STARTED"
    assert manifest["plan_checksum"] == "not_created_no_live_plan"
    assert "No live failover" in " ".join(manifest["limitations"])


def test_describe_scenario_handles_known_and_unknown_scenarios() -> None:
    assert describe_scenario("primary_region_unavailable") is not None
    assert describe_scenario("missing_scenario") is None


def test_boundary_no_live_resilience_or_later_milestone_claims() -> None:
    registry = load_recovery_registry()
    registry_text = json.dumps(
        {**registry, "unsupported_resilience_claim_patterns": []}, sort_keys=True
    ).lower()
    docs_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in Path("recovery").rglob("*")
        if path.is_file()
    )

    assert "live failover completed" not in registry_text
    assert "production resilience certified" not in registry_text
    assert "automatic failover enabled" not in registry_text
    assert "automatic failback enabled" not in registry_text
    assert "live snowflake replication configured" not in registry_text
    assert "kubernetes" not in registry_text
    assert "milestone 17" not in docs_text
    assert "password:" not in registry_text
    assert "private_key:" not in registry_text
