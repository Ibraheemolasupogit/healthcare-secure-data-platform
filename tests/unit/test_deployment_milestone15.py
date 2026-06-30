"""Milestone 15 protected CI/CD and deployment-control tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from healthcare_platform.deployment import (
    build_deployment_evidence,
    detect_drift,
    evaluate_policy_gates,
    load_deployment_registry,
    validate_deployment_controls,
    verify_evidence,
)


def _workflow_yaml(path: str) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def test_deployment_registry_validates_static_control_counts() -> None:
    report = validate_deployment_controls()

    assert report["valid"], report["errors"]
    assert report["workflow_count"] >= 7
    assert report["environment_count"] == 3
    assert report["service_identity_count"] >= 7
    assert report["artifact_count"] >= 5
    assert report["rollback_target_count"] >= 7
    assert report["deployment_status"] == "NOT_DEPLOYED"
    assert report["apply_status"] == "NOT_EXECUTED"


def test_workflows_are_credential_free_and_least_privilege() -> None:
    registry = load_deployment_registry()

    for workflow in registry["workflows"]:
        workflow_path = Path(workflow["path"])
        assert workflow_path.exists()
        text = workflow_path.read_text(encoding="utf-8")
        parsed = _workflow_yaml(workflow["path"])
        assert parsed["permissions"]["contents"] == "read"
        assert "pull_request_target" not in text
        assert "terraform apply" not in text
        assert workflow["production_apply"] is False
        assert workflow["requires_credentials"] is False


def test_production_apply_is_not_automatic_and_promotion_order_is_explicit() -> None:
    registry = load_deployment_registry()
    promotion = registry["promotion"]
    environments = sorted(registry["environments"], key=lambda item: item["order"])

    assert [item["environment"] for item in environments] == ["DEV", "TEST", "PROD"]
    assert promotion["order"] == ["DEV", "TEST", "PROD"]
    assert promotion["exact_commit_required"] is True
    assert promotion["exact_artifact_required"] is True
    assert promotion["no_self_approval"] is True
    assert promotion["failed_validation_blocks_promotion"] is True
    assert promotion["production_auto_apply"] is False
    assert promotion["apply_jobs_enabled"] is False
    assert next(item for item in environments if item["environment"] == "PROD")[
        "separate_reviewer_required"
    ]


def test_branch_environment_and_codeowners_blueprints_are_present() -> None:
    registry = load_deployment_registry()
    branch = registry["branch_protection"]

    assert branch["branch"] == "main"
    assert branch["required_pull_request"] is True
    assert branch["require_codeowners_review"] is True
    assert branch["force_push"] == "prohibited"
    assert branch["branch_deletion"] == "prohibited"
    assert branch["live_configuration_status"] == "blueprint_only"
    assert Path(".github/CODEOWNERS").exists()
    assert "Real GitHub team slugs are intentionally not invented" in Path(
        ".github/CODEOWNERS"
    ).read_text(encoding="utf-8")

    prod = next(item for item in registry["environments"] if item["environment"] == "PROD")
    assert prod["github_environment"] == "hedp-prod"
    assert prod["branch_restrictions"] == "protected_release_tag"
    assert "security_admin" in prod["required_reviewers"]


def test_terraform_validation_contracts_and_state_boundaries() -> None:
    registry = load_deployment_registry()
    terraform = registry["terraform"]

    assert terraform["provider_lock_required"] is True
    assert terraform["backend_disabled_for_local_validation"] is True
    assert terraform["remote_state_design"]["separate_state_per_environment"] is True
    assert terraform["remote_state_design"]["no_state_in_repository"] is True
    assert terraform["remote_state_design"]["no_local_production_state"] is True
    for environment in registry["environments"]:
        terraform_path = Path(environment["terraform_path"])
        assert terraform_path.exists()
        assert (terraform_path / ".terraform.lock.hcl").exists()
        assert environment["apply_status"] == "NOT_EXECUTED"


def test_plan_metadata_and_review_controls_fail_closed() -> None:
    registry = load_deployment_registry()
    terraform = registry["terraform"]

    assert {
        "commit_sha",
        "environment",
        "terraform_version",
        "provider_versions",
        "variable_set_id",
        "plan_checksum",
        "plan_created_at",
        "plan_expires_at",
        "approval_status",
    }.issubset(terraform["plan_metadata_required"])
    review = terraform["plan_review_controls"]
    assert review["destructive_changes_escalate"] is True
    assert review["wildcard_grants_blocked"] is True
    assert review["public_access_blocked"] is True
    assert review["environment_mismatch_blocked"] is True
    assert review["sensitive_output_blocked"] is True


def test_service_identities_are_environment_scoped_and_non_interactive() -> None:
    registry = load_deployment_registry()
    identities = {item["service_id"]: item for item in registry["service_identities"]}

    assert {"svc_terraform_dev", "svc_terraform_test", "svc_terraform_prod"}.issubset(identities)
    assert identities["svc_terraform_dev"]["environment"] == "DEV"
    assert identities["svc_terraform_test"]["environment"] == "TEST"
    assert identities["svc_terraform_prod"]["environment"] == "PROD"
    for identity in identities.values():
        assert identity["interactive_login"] == "prohibited"
        assert identity["deployment_status"] == "not_configured_locally"
        assert "secret" in identity["credential_storage"]


def test_governance_policy_gates_are_invoked() -> None:
    result = evaluate_policy_gates()

    assert result["valid"], result
    assert result["checks"]["governance_registry_valid"] is True
    assert result["checks"]["governance_registry_invoked"] is True
    assert result["checks"]["separation_of_duties_validated"] is True
    assert result["checks"]["unsupported_claims_blocked"] is True
    assert result["checks"]["missing_policy_mapping_fails_closed"] is True


def test_platform_deployment_controls_preserve_existing_ownership() -> None:
    registry = load_deployment_registry()
    controls = registry["platform_controls"]

    assert controls["dbt"]["pr_validation"] == "dbt_parse_and_static_tests"
    assert controls["dbt"]["connected_execution_status"] == "not_executed"
    assert controls["airflow"]["connected_execution_status"] == "not_deployed"
    assert controls["dataiku"]["connected_execution_status"] == "not_deployed"
    assert controls["feature_store"]["connected_execution_status"] == "offline_only"
    assert controls["fabric_powerbi"]["connected_execution_status"] == "not_deployed"


def test_local_drift_simulation_detects_added_and_changed_resources() -> None:
    drift = detect_drift()

    assert drift["mode"] == "local_file_simulation"
    assert drift["automatic_remediation"] is False
    assert drift["status"] == "DRIFT_DETECTED"
    assert drift["severity"] == "MEDIUM"
    assert "HEDP_DEV_UNUSED_LEGACY_ROLE" in drift["added"]
    assert "HEDP_DEV_ANALYTICS_WH_CHANGED" in drift["changed"]
    assert drift["removed"] == []


def test_rollback_requires_approval_and_has_targets() -> None:
    registry = load_deployment_registry()
    rollback = registry["rollback"]
    targets = {item["platform"]: item for item in rollback["targets"]}

    assert rollback["automatic_rollback_enabled"] is False
    assert rollback["approval_required"] is True
    assert rollback["evidence_required"] is True
    assert {
        "terraform",
        "dbt",
        "airflow",
        "dataiku",
        "feature_store",
        "fabric_powerbi",
        "governance",
    }.issubset(targets)
    for target in targets.values():
        assert target["rollback_target"]
        assert target["compatibility_required"]


def test_evidence_generation_outputs_manifests_and_checksums(tmp_path: Path) -> None:
    evidence = build_deployment_evidence(tmp_path, overwrite=True)
    verification = verify_evidence(tmp_path)

    expected = {
        "release_manifest.json",
        "deployment_manifest_dev.json",
        "deployment_manifest_test.json",
        "deployment_manifest_prod.json",
        "terraform_validation_report.json",
        "policy_gate_report.json",
        "artefact_inventory.csv",
        "promotion_matrix.csv",
        "drift_report.json",
        "rollback_plan.md",
        "validation_report.json",
        "validation_report.md",
        "checksums.sha256",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected
    assert evidence.output_dir == tmp_path
    assert verification["valid"], verification["errors"]
    assert verification["checked_files"] == len(expected) - 1

    release = json.loads((tmp_path / "release_manifest.json").read_text(encoding="utf-8"))
    assert release["milestone"] == 15
    assert release["deployment_status"] == "NOT_DEPLOYED"
    assert release["approval_status"] == "NOT_REQUESTED"
    assert release["synthetic_only"] is True

    prod = json.loads((tmp_path / "deployment_manifest_prod.json").read_text(encoding="utf-8"))
    assert prod["environment"] == "PROD"
    assert prod["apply_status"] == "NOT_EXECUTED"
    assert prod["resource_changes"] == {"create": 0, "update": 0, "delete": 0, "replace": 0}


def test_boundary_no_live_deployment_credentials_or_later_scope() -> None:
    workflow_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in Path(".github/workflows").rglob("*.yml")
        if path.is_file()
    )
    registry = load_deployment_registry()
    registry_text = json.dumps(
        {**registry, "unsupported_deployment_claim_patterns": []}, sort_keys=True
    ).lower()

    assert "terraform apply" not in workflow_text
    assert "pull_request_target" not in workflow_text
    assert "production deployed" not in registry_text
    assert "apply succeeded" not in registry_text
    assert "kubernetes deployed" not in registry_text
    assert "multi-region deployment complete" not in registry_text
    assert "disaster recovery implemented" not in registry_text
    assert "password:" not in registry_text
    assert "private_key:" not in registry_text
