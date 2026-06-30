"""Milestone 17 operational observability and recovery-drill tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from healthcare_platform.operations import (
    build_operations_evidence,
    describe_drill,
    evaluate_health,
    load_operations_registry,
    simulate_drill,
    simulate_incident,
    validate_operations_registry,
    verify_evidence,
)


def _ids(items: list[dict[str, Any]], key: str) -> set[str]:
    return {str(item[key]) for item in items}


def test_operations_registry_validates_expected_counts_and_statuses() -> None:
    report = validate_operations_registry()

    assert report["valid"], report["errors"]
    assert report["service_count"] == 14
    assert report["health_check_count"] >= 50
    assert report["sli_count"] >= 14
    assert report["slo_count"] >= 10
    assert report["incident_category_count"] == 14
    assert report["route_count"] == 14
    assert report["runbook_count"] == 12
    assert report["drill_count"] == 10
    assert report["connected_status"] == "NOT_CONNECTED"
    assert report["alerting_status"] == "DISABLED"
    assert report["monitoring_status"] == "LOCAL_SIMULATION_ONLY"


def test_service_registry_has_owners_dependencies_references_and_synthetic_flags() -> None:
    registry = load_operations_registry()
    services = registry["services"]
    service_ids = _ids(services, "service_id")
    check_ids = _ids(registry["health_checks"], "check_id")
    sli_ids = _ids(registry["slis"], "sli_id")
    slo_ids = _ids(registry["slos"], "slo_id")
    runbook_ids = _ids(registry["runbooks"], "runbook_id")

    assert {
        "governance_registry",
        "cicd_controls",
        "terraform_delivery",
        "snowflake_platform",
        "dbt_staging",
        "healthcare_core",
        "billing_finance",
        "assurance_controls",
        "airflow_orchestration",
        "dataiku_analytics",
        "feature_store",
        "fabric_semantic_model",
        "powerbi_reports",
        "recovery_evidence_service",
    } == service_ids
    for service in services:
        assert service["owner_role"]
        assert service["business_owner_role"]
        assert service["synthetic_only"] is True
        assert service["recovery_tier"].startswith("TIER_")
        assert set(service["dependencies"]).issubset(service_ids)
        assert set(service["health_checks"]).issubset(check_ids)
        assert set(service["sli_refs"]).issubset(sli_ids)
        assert set(service["slo_refs"]).issubset(slo_ids)
        assert set(service["runbook_refs"]).issubset(runbook_ids)


def test_health_model_controlled_states_and_baseline_health() -> None:
    registry = load_operations_registry()
    health = evaluate_health()

    assert registry["health_model"]["states"] == [
        "HEALTHY",
        "DEGRADED",
        "UNHEALTHY",
        "UNKNOWN",
        "MAINTENANCE",
        "NOT_APPLICABLE",
    ]
    assert registry["health_model"]["precedence"][0] == "UNHEALTHY"
    assert registry["health_model"]["live_health_claim"] is False
    assert health["overall_state"] == "HEALTHY"
    assert set(health["service_states"].values()) == {"HEALTHY"}
    assert health["synthetic"] is True
    assert health["live_monitoring"] is False


def test_dependency_failure_degrades_consumers_deterministically() -> None:
    health = evaluate_health(["chk_snowflake_contract_available"])

    assert health["service_states"]["snowflake_platform"] == "UNHEALTHY"
    assert health["service_states"]["dbt_staging"] == "DEGRADED"
    assert health["service_states"]["healthcare_core"] == "DEGRADED"
    assert health["overall_state"] == "UNHEALTHY"


def test_unknown_state_never_promotes_to_healthy() -> None:
    registry = load_operations_registry()
    assert "UNKNOWN" in registry["health_model"]["precedence"]
    assert registry["health_model"]["precedence"].index("UNKNOWN") < registry["health_model"][
        "precedence"
    ].index("HEALTHY")


def test_sli_slo_and_error_budget_metadata_are_synthetic_only() -> None:
    registry = load_operations_registry()
    sli_ids = _ids(registry["slis"], "sli_id")

    for sli in registry["slis"]:
        assert sli["sli_id"] in sli_ids
        assert sli["owner"]
        assert "live" not in sli["implementation_status"]
    for slo in registry["slos"]:
        assert slo["sli_ref"] in sli_ids
        assert slo["synthetic_target"] is True
        assert float(slo["warning_threshold"]) >= float(slo["failure_threshold"])
        assert any(
            phrase in slo["limitations"].lower() for phrase in ("not", "local", "only", "no ")
        )
    for budget in registry["error_budgets"]:
        assert budget["consumed_budget"] <= budget["allowed_failure_budget"]
        assert budget["remaining_budget"] >= 0
        assert budget["breach_status"] == "within_budget"


def test_incident_taxonomy_routes_and_lifecycle_are_complete() -> None:
    registry = load_operations_registry()
    categories = set(registry["incident_categories"])
    routed_categories = {route["incident_type"] for route in registry["alert_routes"]}
    transitions = registry["incident_lifecycle"]["transitions"]

    assert categories == routed_categories
    assert "SEV_1_CRITICAL" in {
        level["severity_id"] for level in registry["severity_model"]["levels"]
    }
    assert transitions["DETECTED"] == ["TRIAGED", "FALSE_POSITIVE"]
    assert "CLOSED" in transitions["RESOLVED"]
    for route in registry["alert_routes"]:
        assert route["notification_status"] == "disabled"
        assert route["live_integration_status"] == "disabled"
        assert route["runbook"].startswith("rb_")


def test_incident_simulation_classifies_routes_runbooks_and_payload_boundary() -> None:
    incident = simulate_incident()

    assert incident["severity"] == "SEV_1_CRITICAL"
    assert incident["expected_severity"] == "SEV_1_CRITICAL"
    assert incident["route"]["route_id"] == "route_access_control_critical"
    assert incident["runbook"]["runbook_id"] == "rb_governance_checksum_mismatch"
    assert incident["lifecycle_transitions_valid"] is True
    assert incident["escalation_required"] is True
    assert incident["contains_patient_payload"] is False
    assert incident["live_alert_created"] is False
    assert incident["ticket_created"] is False


def test_runbook_catalogue_has_required_operational_sections() -> None:
    registry = load_operations_registry()

    for runbook in registry["runbooks"]:
        assert runbook["trigger"] in registry["incident_categories"]
        assert runbook["owner"]
        assert runbook["prerequisites"]
        assert runbook["diagnostic_steps"]
        assert runbook["containment"]
        assert runbook["recovery_steps"]
        assert runbook["validation"]
        assert runbook["escalation"]
        assert runbook["evidence"]
        assert runbook["limitations"]
        assert runbook["execution_status"] in {
            "local_guidance_only",
            "local_simulation_only",
        }


def test_recovery_drills_require_approval_and_no_automatic_execution() -> None:
    registry = load_operations_registry()

    for drill in registry["drills"]:
        assert drill["required_approvals"]
        assert drill["rto_target_minutes"] > 0
        assert drill["rpo_target_minutes"] >= 0
        assert drill["expected_runbook"].startswith("rb_")
        assert drill["schedule_metadata"]["approval_requirement"] == "manual"
        assert drill["schedule_metadata"]["automatic_execution"] is False
        assert drill["schedule_metadata"]["allowed_environment"] == "local_simulation"
        assert any(
            phrase in drill["limitations"].lower()
            for phrase in ("no live", "no ", "metadata only", "simulation")
        )


def test_drill_simulation_evaluates_rto_rpo_and_never_calls_cloud() -> None:
    drill = simulate_drill()

    assert drill["status"] == "DRILL_READY_WITH_APPROVAL"
    assert drill["expected_status"] == "DRILL_READY_WITH_APPROVAL"
    assert drill["rto_met"] is True
    assert drill["rpo_met"] is True
    assert drill["approval_required"] is True
    assert drill["cloud_action_performed"] is False
    assert drill["automatic_execution"] is False
    assert drill["live_failover_executed"] is False
    assert drill["runbook"]["runbook_id"] == "rb_regional_recovery_drill"


def test_describe_drill_handles_known_and_unknown_drills() -> None:
    assert describe_drill("drill_primary_region_outage") is not None
    assert describe_drill("missing_drill") is None


def test_operations_evidence_generation_outputs_expected_files(tmp_path: Path) -> None:
    evidence = build_operations_evidence(tmp_path, overwrite=True)
    verification = verify_evidence(tmp_path)

    expected = {
        "service_registry.json",
        "health_check_catalogue.csv",
        "sli_catalogue.csv",
        "slo_catalogue.csv",
        "incident_taxonomy.json",
        "alert_routing.csv",
        "runbook_catalogue.csv",
        "drill_catalogue.json",
        "health_report.json",
        "incident_simulation.json",
        "drill_simulation.json",
        "post_incident_review.md",
        "validation_report.json",
        "validation_report.md",
        "evidence_manifest.json",
        "checksums.sha256",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected
    assert evidence.output_dir == tmp_path
    assert verification["valid"], verification["errors"]
    assert verification["checked_files"] == len(expected) - 1

    manifest = json.loads((tmp_path / "evidence_manifest.json").read_text(encoding="utf-8"))
    assert manifest["synthetic"] is True
    assert manifest["local_simulation"] is True
    assert manifest["live_monitoring"] is False
    assert manifest["live_alerts"] is False
    assert manifest["production_slo_commitment"] is False
    assert manifest["clinical_assurance_claim"] is False


def test_evidence_contains_no_credentials_real_identities_or_live_alert_claims() -> None:
    registry_text = json.dumps(load_operations_registry(), sort_keys=True).lower()
    evidence_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in Path("operations/reference").rglob("*")
        if path.is_file()
    )
    combined = registry_text + "\n" + evidence_text

    forbidden = [
        "webhook_url",
        "client_secret",
        "secret_access_key",
        "password:",
        "@example.com",
        "pagerduty enabled",
        "slack alerts enabled",
        "teams alerts enabled",
        "servicenow ticket created",
        "live alert created",
        "automatic remediation enabled",
        "live failover executed",
        "production slo is guaranteed",
        "clinical assurance certified",
    ]
    for phrase in forbidden:
        assert phrase not in combined


def test_boundary_no_live_observability_platform_or_later_milestone_claims() -> None:
    registry = load_operations_registry()
    registry_text = json.dumps(registry, sort_keys=True).lower()
    operations_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in Path("operations").rglob("*")
        if path.is_file()
    )

    assert registry["live_integrations"] == {
        "siem": "disabled",
        "pagerduty": "disabled",
        "slack": "disabled",
        "teams": "disabled",
        "email": "disabled",
        "servicenow": "disabled",
        "cloud_monitoring": "disabled",
    }
    assert registry["automatic_remediation_enabled"] is False
    assert registry["automatic_production_drills_enabled"] is False
    assert "prometheus" not in registry_text
    assert "grafana" not in registry_text
    assert "datadog" not in registry_text
    assert "splunk" not in registry_text
    assert "opentelemetry" not in registry_text
    assert "milestone 18" not in operations_text
