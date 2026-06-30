"""Local deployment-control validation and evidence generation."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from healthcare_platform.governance import validate_registry as validate_governance_registry

REGISTRY_PATH = Path("deployment/registry/deployment_controls.yaml")
REFERENCE_DIR = Path("deployment/reference")
ENVIRONMENTS = ("DEV", "TEST", "PROD")
LOCAL_TIMESTAMP = "2026-06-28T00:00:00Z"


@dataclass(frozen=True)
class DeploymentEvidence:
    """Generated deployment evidence paths."""

    output_dir: Path
    validation_report: Path
    release_manifest: Path
    checksums: Path


def _read_yaml(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _git_commit_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN_LOCAL_COMMIT"
    return result.stdout.strip()


def load_deployment_registry() -> dict[str, Any]:
    """Load the central deployment-control registry."""
    return _read_yaml(REGISTRY_PATH)


def detect_drift(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run deterministic file-based drift simulation."""
    controls = registry or load_deployment_registry()
    expected = set(controls["drift"]["expected_resources"])
    observed = set(controls["drift"]["observed_resources"])
    changed_bases = {
        item.removesuffix("_CHANGED")
        for item in observed
        if item.endswith("_CHANGED") and item.removesuffix("_CHANGED") in expected
    }
    added = sorted(
        (observed - expected) - set(item for item in observed if item.endswith("_CHANGED"))
    )
    removed = sorted(expected - observed - changed_bases)
    changed = sorted(
        item
        for item in observed
        if item.endswith("_CHANGED") and item.removesuffix("_CHANGED") in expected
    )
    severity = "HIGH" if removed else "MEDIUM" if added or changed else "NONE"
    return {
        "mode": controls["drift"]["mode"],
        "automatic_remediation": controls["drift"]["automatic_remediation"],
        "added": added,
        "removed": removed,
        "changed": changed,
        "severity": severity,
        "status": "DRIFT_DETECTED" if added or removed or changed else "NO_DRIFT",
        "limitations": "Local file-based simulation; no live infrastructure queried.",
    }


def evaluate_policy_gates() -> dict[str, Any]:
    """Evaluate local deployment policy gates."""
    controls = load_deployment_registry()
    governance = validate_governance_registry()
    gates = controls["policy_gates"]
    checks = {
        "governance_registry_valid": governance["valid"],
        "governance_registry_invoked": gates["governance_registry_invoked"],
        "service_identity_allowed": gates["service_identity_allowed"],
        "purpose_allowed": gates["purpose_allowed"],
        "environment_allowed": gates["environment_allowed"],
        "separation_of_duties_validated": gates["separation_of_duties_validated"],
        "unsupported_claims_blocked": gates["unsupported_claims_blocked"],
        "missing_policy_mapping_fails_closed": gates["missing_policy_mapping_fails_closed"],
    }
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "limitations": "Local static policy-gate evaluation; not a live deployment approval.",
    }


def _workflow_paths(controls: dict[str, Any]) -> list[Path]:
    return [Path(workflow["path"]) for workflow in controls["workflows"]]


def _scan_workflow_text(paths: list[Path]) -> str:
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)


def validate_deployment_controls() -> dict[str, Any]:
    """Validate deployment-control metadata and static CI/CD guardrails."""
    controls = load_deployment_registry()
    errors: list[str] = []
    warnings: list[str] = []

    if controls["deployment_status"] != "NOT_DEPLOYED":
        errors.append("deployment status must remain NOT_DEPLOYED")
    if controls["apply_status"] != "NOT_EXECUTED":
        errors.append("apply status must remain NOT_EXECUTED")

    workflows = controls["workflows"]
    workflow_ids = [workflow["workflow_id"] for workflow in workflows]
    if len(workflow_ids) != len(set(workflow_ids)):
        errors.append("workflow IDs must be unique")
    for path in _workflow_paths(controls):
        if not path.exists():
            errors.append(f"workflow path missing: {path}")

    workflow_text = _scan_workflow_text(
        [path for path in _workflow_paths(controls) if path.exists()]
    )
    if "pull_request_target:" in workflow_text:
        errors.append("pull_request_target is prohibited")
    if re.search(r"permissions:\s*\n\s*contents:\s*write", workflow_text):
        errors.append("broad contents write permission detected")
    if re.search(r"terraform\s+apply", workflow_text):
        errors.append("terraform apply must not appear in workflows for this milestone")
    if (
        re.search(r"environment:\s*hedp-prod", workflow_text)
        and "workflow_dispatch" not in workflow_text
    ):
        errors.append("production environment references require manual dispatch")

    environments = controls["environments"]
    if [item["environment"] for item in sorted(environments, key=lambda e: e["order"])] != list(
        ENVIRONMENTS
    ):
        errors.append("promotion order must be DEV, TEST, PROD")
    for environment in environments:
        terraform_path = Path(environment["terraform_path"])
        if not terraform_path.exists():
            errors.append(f"terraform path missing: {terraform_path}")
        if not (terraform_path / ".terraform.lock.hcl").exists():
            errors.append(f"provider lock file missing: {terraform_path}")
        if environment["apply_status"] != "NOT_EXECUTED":
            errors.append(f"{environment['environment']} apply status must be NOT_EXECUTED")
        if not environment.get("required_reviewers"):
            errors.append(f"{environment['environment']} missing reviewers")
    prod = next(item for item in environments if item["environment"] == "PROD")
    if prod.get("separate_reviewer_required") is not True:
        errors.append("PROD must require separate reviewer")

    promotion = controls["promotion"]
    if promotion["order"] != list(ENVIRONMENTS):
        errors.append("promotion.order must be DEV, TEST, PROD")
    for required in (
        "exact_commit_required",
        "exact_artifact_required",
        "no_self_approval",
        "failed_validation_blocks_promotion",
    ):
        if promotion[required] is not True:
            errors.append(f"promotion {required} must be true")
    if promotion["production_auto_apply"] or promotion["apply_jobs_enabled"]:
        errors.append("automatic or enabled apply jobs are prohibited")

    for service in controls["service_identities"]:
        if service["interactive_login"] != "prohibited":
            errors.append(f"service identity {service['service_id']} allows interactive login")
        if service["deployment_status"] != "not_configured_locally":
            errors.append(f"service identity {service['service_id']} claims live configuration")

    if not evaluate_policy_gates()["valid"]:
        errors.append("policy gates failed")

    claim_scan_controls = dict(controls)
    claim_scan_controls["unsupported_deployment_claim_patterns"] = []
    text = json.dumps(claim_scan_controls, sort_keys=True).lower()
    for pattern in controls["unsupported_deployment_claim_patterns"]:
        if pattern in text:
            errors.append(f"unsupported deployment claim present: {pattern}")
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        errors.append("real email-like value detected")
    if re.search(
        r"(?i)(password|token|secret|private_key)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{8,}", text
    ):
        errors.append("credential-like value detected")

    drift = detect_drift(controls)
    if drift["automatic_remediation"] is not False:
        errors.append("drift remediation must not be automatic")
    if controls["rollback"]["automatic_rollback_enabled"] is not False:
        errors.append("automatic rollback must be disabled")
    if controls["rollback"]["approval_required"] is not True:
        errors.append("rollback approval must be required")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "workflow_count": len(workflows),
        "environment_count": len(environments),
        "service_identity_count": len(controls["service_identities"]),
        "artifact_count": len(controls["artifact_inventory"]),
        "rollback_target_count": len(controls["rollback"]["targets"]),
        "deployment_status": controls["deployment_status"],
        "apply_status": controls["apply_status"],
    }


def _deployment_manifest(controls: dict[str, Any], environment: dict[str, Any]) -> dict[str, Any]:
    env = environment["environment"]
    return {
        "deployment_id": f"m15-{env.lower()}-not-executed",
        "release_id": controls["release"]["release_id"],
        "environment": env,
        "plan_artifact": f"terraform_plan_{env.lower()}.tfplan",
        "plan_checksum": f"not_created_no_live_credentials_{env.lower()}",
        "apply_status": "NOT_EXECUTED",
        "actor_type": "service_identity_when_approved",
        "service_identity": environment["service_identity"],
        "approval_references": environment["required_reviewers"],
        "start_time": None,
        "end_time": None,
        "resource_changes": {"create": 0, "update": 0, "delete": 0, "replace": 0},
        "dbt_artifacts": "manifest_checksum_required_before_connected_execution",
        "airflow_bundle": "dag_bundle_checksum_required_before_deployment",
        "dataiku_bundle": "project_bundle_identifier_required_before_deployment",
        "feature_store_version": "feature_registry_version_required_before_deployment",
        "powerbi_artifact_version": "semantic_model_artifact_version_required_before_deployment",
        "evidence_references": ["deployment/reference/validation_report.json"],
        "rollback_reference": "deployment/reference/rollback_plan.md",
        "limitations": "Local manifest only; no apply or live deployment executed.",
    }


def _write_checksums(output_dir: Path, files: list[Path]) -> Path:
    path = output_dir / "checksums.sha256"
    path.write_text(
        "\n".join(f"{_sha256(file)}  {file.name}" for file in sorted(files)) + "\n",
        encoding="utf-8",
    )
    return path


def build_deployment_evidence(
    output_dir: Path = REFERENCE_DIR, *, overwrite: bool = False
) -> DeploymentEvidence:
    """Generate deterministic local deployment-control evidence."""
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise ValueError(f"{output_dir} already contains files; pass --overwrite")
    output_dir.mkdir(parents=True, exist_ok=True)

    controls = load_deployment_registry()
    validation = validate_deployment_controls()
    commit_sha = _git_commit_sha()
    tool_versions = {
        "python": "local",
        "terraform_required": controls["terraform"]["required_version"],
        "registry_version": controls["version"],
    }

    release_manifest = output_dir / "release_manifest.json"
    release_manifest.write_text(
        json.dumps(
            {
                "release_id": controls["release"]["release_id"],
                "repository": controls["repository"],
                "commit_sha": commit_sha,
                "branch": "main",
                "milestone": controls["milestone"],
                "version": controls["release"]["version"],
                "environments_targeted": list(ENVIRONMENTS),
                "artifacts": controls["artifact_inventory"],
                "tool_versions": tool_versions,
                "governance_validation_status": evaluate_policy_gates()["checks"][
                    "governance_registry_valid"
                ],
                "test_status": "passed_locally_when_make_validate_succeeds",
                "deployment_status": controls["deployment_status"],
                "approval_status": "NOT_REQUESTED",
                "rollback_version": "previous_reviewed_release_manifest",
                "known_limitations": [
                    "No live credentials used.",
                    "No Terraform apply executed.",
                    "No production deployment occurred.",
                ],
                "synthetic_only": True,
                "created_at": LOCAL_TIMESTAMP,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    deployment_files: list[Path] = []
    for environment in controls["environments"]:
        path = output_dir / f"deployment_manifest_{environment['environment'].lower()}.json"
        path.write_text(
            json.dumps(_deployment_manifest(controls, environment), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        deployment_files.append(path)

    terraform_report = output_dir / "terraform_validation_report.json"
    terraform_report.write_text(
        json.dumps(
            {
                "status": "STATICALLY_VALIDATED",
                "terraform_available_locally": None,
                "backend_disabled_for_local_validation": True,
                "environments": [
                    {
                        "environment": env["environment"],
                        "path": env["terraform_path"],
                        "lock_file_present": (
                            Path(env["terraform_path"]) / ".terraform.lock.hcl"
                        ).exists(),
                        "plan_status": "NOT_CREATED_NO_LIVE_CREDENTIALS",
                        "apply_status": env["apply_status"],
                    }
                    for env in controls["environments"]
                ],
                "limitations": "Real plan/apply requires protected credentials and approval.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    policy_gate_report = output_dir / "policy_gate_report.json"
    policy_gate_report.write_text(
        json.dumps(evaluate_policy_gates(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_csv(
        output_dir / "artefact_inventory.csv",
        controls["artifact_inventory"],
        ["artifact_id", "source_path", "checksum_required", "retention"],
    )
    _write_csv(
        output_dir / "promotion_matrix.csv",
        controls["environments"],
        [
            "environment",
            "order",
            "terraform_path",
            "github_environment",
            "service_identity",
            "apply_status",
        ],
    )
    drift_report = output_dir / "drift_report.json"
    drift_report.write_text(
        json.dumps(detect_drift(controls), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    rollback_plan = output_dir / "rollback_plan.md"
    rollback_plan.write_text(
        "\n".join(
            [
                "# Rollback plan",
                "",
                "Automatic rollback is disabled. Rollback requires approval, compatibility review,",
                "evidence capture and post-rollback validation.",
                "",
                *[
                    f"- {target['platform']}: target `{target['rollback_target']}`, "
                    f"compatibility `{target['compatibility_required']}`."
                    for target in controls["rollback"]["targets"]
                ],
                "",
            ]
        ),
        encoding="utf-8",
    )
    validation_report = output_dir / "validation_report.json"
    validation_report.write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    validation_md = output_dir / "validation_report.md"
    validation_md.write_text(
        "\n".join(
            [
                "# Deployment validation report",
                "",
                "- Local deterministic deployment-control evidence.",
                "- Synthetic portfolio only.",
                "- Statically validated; not deployed and not applied.",
                "- No live credentials used.",
                f"- Valid: {validation['valid']}",
                f"- Workflows: {validation['workflow_count']}",
                f"- Environments: {validation['environment_count']}",
                f"- Service identities: {validation['service_identity_count']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    files = [
        release_manifest,
        *deployment_files,
        terraform_report,
        policy_gate_report,
        output_dir / "artefact_inventory.csv",
        output_dir / "promotion_matrix.csv",
        drift_report,
        rollback_plan,
        validation_report,
        validation_md,
    ]
    checksums = _write_checksums(output_dir, files)
    return DeploymentEvidence(output_dir, validation_report, release_manifest, checksums)


def verify_evidence(output_dir: Path = REFERENCE_DIR) -> dict[str, Any]:
    """Verify generated deployment evidence checksums."""
    checksum_path = output_dir / "checksums.sha256"
    errors: list[str] = []
    if not checksum_path.exists():
        return {"valid": False, "errors": [f"missing {checksum_path}"], "checked_files": 0}
    lines = checksum_path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        expected, filename = line.split("  ", maxsplit=1)
        path = output_dir / filename
        if not path.exists():
            errors.append(f"missing {filename}")
        elif _sha256(path) != expected:
            errors.append(f"checksum mismatch {filename}")
    return {"valid": not errors, "errors": errors, "checked_files": len(lines)}
