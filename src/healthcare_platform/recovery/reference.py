"""Local recovery registry validation, simulation and evidence generation."""

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

REGISTRY_PATH = Path("recovery/registry/recovery_controls.yaml")
REFERENCE_DIR = Path("recovery/reference")
LOCAL_TIMESTAMP = "2026-06-30T00:00:00Z"


@dataclass(frozen=True)
class RecoveryEvidence:
    """Generated recovery evidence paths."""

    output_dir: Path
    validation_report: Path
    recovery_manifest: Path
    checksums: Path


def _read_yaml(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_recovery_registry() -> dict[str, Any]:
    """Load the central recovery registry."""
    return _read_yaml(REGISTRY_PATH)


def _ids(items: list[dict[str, Any]], key: str) -> set[str]:
    return {str(item[key]) for item in items}


def _topological_order(nodes: list[str], edges: list[list[str]]) -> list[str]:
    incoming: dict[str, set[str]] = {node: set() for node in nodes}
    outgoing: dict[str, set[str]] = {node: set() for node in nodes}
    for source, target in edges:
        incoming[target].add(source)
        outgoing[source].add(target)
    ready = sorted(node for node, dependencies in incoming.items() if not dependencies)
    ordered: list[str] = []
    while ready:
        node = ready.pop(0)
        ordered.append(node)
        for target in sorted(outgoing[node]):
            incoming[target].remove(node)
            if not incoming[target]:
                ready.append(target)
        ready.sort()
    if len(ordered) != len(nodes):
        raise ValueError("dependency graph contains a cycle")
    return ordered


def _max_tier_targets(registry: dict[str, Any], affected_services: list[str]) -> tuple[int, int]:
    tiers = registry["recovery_tiers"]
    matched = [
        tier
        for tier in tiers
        if any(service in set(tier["services"]) for service in affected_services)
    ]
    if not matched:
        return 1440, 1440
    return min(tier["rto_minutes"] for tier in matched), min(
        tier["rpo_minutes"] for tier in matched
    )


def describe_scenario(scenario_id: str) -> dict[str, Any] | None:
    """Return a recovery scenario by ID."""
    for scenario in load_recovery_registry()["recovery_scenarios"]:
        if scenario["scenario_id"] == scenario_id:
            return cast(dict[str, Any], scenario)
    return None


def simulate_failover(scenario_id: str = "primary_region_unavailable") -> dict[str, Any]:
    """Run deterministic local failover simulation."""
    registry = load_recovery_registry()
    scenario = describe_scenario(scenario_id)
    if scenario is None:
        raise ValueError(f"unknown recovery scenario: {scenario_id}")
    graph = registry["dependency_graph"]
    _topological_order(graph["nodes"], graph["edges"])
    rto_target, rpo_target = _max_tier_targets(registry, scenario["affected_services"])
    dependency_overrides = scenario.get("dependency_overrides", {})

    if dependency_overrides.get("governance_registry") == "checksum_mismatch":
        status = "RECOVERY_BLOCKED"
        decision = "Fail closed until governance policy integrity is restored."
    elif scenario["recovery_point_age_minutes"] > rpo_target:
        status = "RPO_BREACH"
        decision = "Reject failover until a valid recovery point is available."
    elif scenario["simulated_duration_minutes"] > rto_target:
        status = "RTO_BREACH"
        decision = "Escalate because simulated duration exceeds target."
    else:
        status = "RECOVERY_READY_WITH_APPROVAL"
        decision = "Manual approval required before any live failover action."

    steps = [
        {
            "step": index + 1,
            "component": component,
            "action": "validate_and_restore_metadata_only",
        }
        for index, component in enumerate(registry["recovery_order"])
    ]
    return {
        "scenario_id": scenario_id,
        "trigger": scenario["trigger"],
        "status": status,
        "expected_status": scenario["expected_status"],
        "decision_reason": decision,
        "primary_region": registry["regional_design"]["primary_region"],
        "recovery_region": registry["regional_design"]["recovery_region"],
        "approval_required": registry["failover_criteria"]["approval_required"],
        "automatic_failover_enabled": registry["failover_criteria"]["automatic_failover_enabled"],
        "rto_target_minutes": rto_target,
        "rpo_target_minutes": rpo_target,
        "simulated_duration_minutes": scenario["simulated_duration_minutes"],
        "recovery_point_age_minutes": scenario["recovery_point_age_minutes"],
        "ordered_recovery_steps": steps,
        "limitations": "Local deterministic simulation only; no cloud action performed.",
        "synthetic": True,
    }


def validate_recovery_registry() -> dict[str, Any]:
    """Validate recovery metadata and scope boundaries."""
    registry = load_recovery_registry()
    errors: list[str] = []
    warnings: list[str] = []

    if registry["live_deployment_status"] != "NOT_DEPLOYED":
        errors.append("live deployment status must remain NOT_DEPLOYED")
    if registry["regional_design"]["automatic_failover_enabled"] is not False:
        errors.append("automatic failover must be disabled")
    if registry["regional_design"]["automatic_failback_enabled"] is not False:
        errors.append("automatic failback must be disabled")

    region_ids = _ids(registry["region_classes"], "region_id")
    tier_ids = _ids(registry["recovery_tiers"], "tier_id")
    scenario_ids = _ids(registry["recovery_scenarios"], "scenario_id")
    if len(region_ids) != len(registry["region_classes"]):
        errors.append("region IDs must be unique")
    if len(tier_ids) != len(registry["recovery_tiers"]):
        errors.append("tier IDs must be unique")
    if len(scenario_ids) != len(registry["recovery_scenarios"]):
        errors.append("scenario IDs must be unique")

    for region_id in region_ids:
        if region_id not in {"PRIMARY_REGION", "RECOVERY_REGION", "ARCHIVAL_REGION"}:
            errors.append(f"non-symbolic region id detected: {region_id}")

    for tier in registry["recovery_tiers"]:
        if tier["rto_minutes"] <= 0 or tier["rpo_minutes"] < 0:
            errors.append(f"invalid RTO/RPO for {tier['tier_id']}")
        if not tier["owner"]:
            errors.append(f"tier {tier['tier_id']} missing owner")
        for dependency in tier["recovery_dependencies"]:
            if dependency not in tier_ids:
                errors.append(f"tier {tier['tier_id']} references unknown dependency")

    retention_ids = {
        item["retention_policy_id"]
        for item in _read_yaml(Path("governance/registry/retention_policies.yaml"))[
            "retention_policies"
        ]
    }
    export_ids = {
        item["export_policy_id"]
        for item in _read_yaml(Path("governance/registry/export_policies.yaml"))["export_policies"]
    }
    for policy in registry["residency_policies"]:
        if not set(policy["allowed_region_class"]).issubset(region_ids):
            errors.append(f"residency policy {policy['policy_id']} has bad allowed region")
        if not set(policy["prohibited_region_class"]).issubset(region_ids):
            errors.append(f"residency policy {policy['policy_id']} has bad prohibited region")
        if policy["export_restriction"] not in export_ids:
            errors.append(f"residency policy {policy['policy_id']} bad export policy")
        if policy["retention_policy_ref"] not in retention_ids:
            errors.append(f"residency policy {policy['policy_id']} bad retention policy")
        if "legal_review_required" not in policy:
            errors.append(f"residency policy {policy['policy_id']} missing legal review flag")

    graph = registry["dependency_graph"]
    nodes = set(graph["nodes"])
    for source, target in graph["edges"]:
        if source not in nodes or target not in nodes:
            errors.append(f"dependency edge does not resolve: {source}->{target}")
    try:
        ordered = _topological_order(graph["nodes"], graph["edges"])
    except ValueError as error:
        errors.append(str(error))
        ordered = []
    if ordered and registry["recovery_order"][0] != "governance_registry":
        errors.append("recovery must start with governance registry")
    if ordered and registry["recovery_order"].index("fabric_powerbi") < registry[
        "recovery_order"
    ].index("healthcare_core"):
        errors.append("consumer layer cannot recover before healthcare core")

    required_platforms = {
        "snowflake",
        "dbt",
        "airflow",
        "dataiku",
        "feature_store",
        "fabric_powerbi",
        "governance",
        "deployment_controls",
    }
    if set(registry["platform_mappings"]) != required_platforms:
        errors.append("platform recovery mappings incomplete")
    for mapping in registry["platform_mappings"].values():
        if mapping["tier"] not in tier_ids:
            errors.append("platform mapping references unknown tier")
        live_status = mapping.get(
            "live_execution_status", mapping.get("live_replication_status", "")
        )
        if "live" in live_status and live_status != "local_registry_only":
            warnings.append("live wording appears only as a negative status")

    if registry["failover_criteria"]["automatic_failover_enabled"] is not False:
        errors.append("failover must not be automatic")
    if registry["failover_criteria"]["approval_required"] is not True:
        errors.append("failover approval must be required")
    if registry["failback"]["automatic_failback_enabled"] is not False:
        errors.append("failback must not be automatic")
    if registry["failback"]["approval_required"] is not True:
        errors.append("failback approval must be required")
    if registry["failback"]["data_reconciliation_required"] is not True:
        errors.append("failback requires data reconciliation")
    if registry["failback"]["stability_period_hours"] <= 0:
        errors.append("failback requires a stability period")

    claim_scan_registry = dict(registry)
    claim_scan_registry["unsupported_resilience_claim_patterns"] = []
    claim_text = json.dumps(claim_scan_registry, sort_keys=True).lower()
    for pattern in registry["unsupported_resilience_claim_patterns"]:
        if pattern in claim_text:
            errors.append(f"unsupported resilience claim present: {pattern}")
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", claim_text):
        errors.append("real email-like value detected")
    if re.search(
        r"(?i)(password|token|secret|private_key)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{8,}", claim_text
    ):
        errors.append("credential-like value detected")

    for scenario in registry["recovery_scenarios"]:
        result = simulate_failover(scenario["scenario_id"])
        if result["status"] != scenario["expected_status"]:
            errors.append(f"scenario {scenario['scenario_id']} did not match expected status")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "region_count": len(region_ids),
        "tier_count": len(tier_ids),
        "residency_policy_count": len(registry["residency_policies"]),
        "dependency_node_count": len(nodes),
        "scenario_count": len(scenario_ids),
        "platform_mapping_count": len(registry["platform_mappings"]),
        "live_deployment_status": registry["live_deployment_status"],
        "simulation_status": registry["simulation_status"],
    }


def _recovery_manifest(registry: dict[str, Any], simulation: dict[str, Any]) -> dict[str, Any]:
    scenario = describe_scenario(simulation["scenario_id"])
    if scenario is None:
        raise ValueError(f"unknown recovery scenario: {simulation['scenario_id']}")
    return {
        "recovery_id": "m16-local-recovery-simulation",
        "incident_id": "synthetic-incident-primary-region",
        "scenario_id": simulation["scenario_id"],
        "primary_region": simulation["primary_region"],
        "recovery_region": simulation["recovery_region"],
        "recovery_tier": "TIER_1_CRITICAL_DATA_SERVICES",
        "affected_services": scenario["affected_services"],
        "release_id": "m15-local-reference",
        "commit_sha": _git_commit_sha(),
        "plan_checksum": "not_created_no_live_plan",
        "policy_registry_checksum": _sha256(Path("governance/reference/policy_registry.json")),
        "source_data_checkpoint": "synthetic_reference_checkpoint",
        "target_recovery_point": "local_simulated_recovery_point",
        "rto_target_minutes": simulation["rto_target_minutes"],
        "rpo_target_minutes": simulation["rpo_target_minutes"],
        "actual_simulated_recovery_duration_minutes": simulation["simulated_duration_minutes"],
        "status": simulation["status"],
        "approval_state": "APPROVAL_REQUIRED_NOT_REQUESTED",
        "validation_results": "local_static_validation",
        "failback_status": "NOT_STARTED",
        "evidence_references": ["recovery/reference/recovery_validation_report.json"],
        "limitations": [
            "Synthetic local simulation only.",
            "No live failover, replication or regional deployment was executed.",
            "RTO/RPO values are portfolio targets, not organisational commitments.",
        ],
        "synthetic": registry["regional_design"]["synthetic_only"],
    }


def _write_checksums(output_dir: Path, files: list[Path]) -> Path:
    path = output_dir / "checksums.sha256"
    path.write_text(
        "\n".join(f"{_sha256(file)}  {file.name}" for file in sorted(files)) + "\n",
        encoding="utf-8",
    )
    return path


def build_recovery_evidence(
    output_dir: Path = REFERENCE_DIR, *, overwrite: bool = False
) -> RecoveryEvidence:
    """Generate deterministic local recovery evidence."""
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise ValueError(f"{output_dir} already contains files; pass --overwrite")
    output_dir.mkdir(parents=True, exist_ok=True)
    registry = load_recovery_registry()
    simulation = simulate_failover()
    validation = validate_recovery_registry()

    region_registry = output_dir / "region_registry.json"
    region_registry.write_text(
        json.dumps(registry["region_classes"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_csv(
        output_dir / "residency_policy.csv",
        registry["residency_policies"],
        [
            "policy_id",
            "data_domain",
            "sensitivity",
            "allowed_region_class",
            "prohibited_region_class",
            "replication_allowed",
            "backup_allowed",
            "export_restriction",
            "retention_policy_ref",
            "legal_review_required",
            "implementation_status",
        ],
    )
    _write_csv(
        output_dir / "recovery_tiers.csv",
        registry["recovery_tiers"],
        [
            "tier_id",
            "services",
            "maximum_tolerable_downtime_minutes",
            "rto_minutes",
            "rpo_minutes",
            "recovery_priority",
            "failover_approval_level",
            "test_frequency",
            "owner",
        ],
    )
    dependency_graph = output_dir / "dependency_graph.json"
    dependency_graph.write_text(
        json.dumps(registry["dependency_graph"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    recovery_scenarios = output_dir / "recovery_scenarios.json"
    recovery_scenarios.write_text(
        json.dumps(registry["recovery_scenarios"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    failover_report = output_dir / "failover_decision_report.json"
    failover_report.write_text(
        json.dumps(simulation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    recovery_manifest = output_dir / "recovery_manifest.json"
    recovery_manifest.write_text(
        json.dumps(_recovery_manifest(registry, simulation), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    validation_report = output_dir / "recovery_validation_report.json"
    validation_report.write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    failback_plan = output_dir / "failback_plan.md"
    failback_plan.write_text(
        "\n".join(
            [
                "# Failback plan",
                "",
                "- Manual approval required.",
                f"- Stability period: {registry['failback']['stability_period_hours']} hours.",
                "- Primary-region integrity checks and data reconciliation are required.",
                "- Reverse replication must be reviewed before traffic restoration.",
                "- Failed failback returns to the recovery region and reopens validation.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    summary = output_dir / "recovery_summary.md"
    summary.write_text(
        "\n".join(
            [
                "# Recovery summary",
                "",
                "- Synthetic local simulation only.",
                "- Not deployed and not live tested.",
                "- Not a production RTO/RPO commitment.",
                "- Not legal advice and not certification evidence.",
                f"- Validation valid: {validation['valid']}",
                f"- Scenario: {simulation['scenario_id']}",
                f"- Simulation status: {simulation['status']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    files = [
        region_registry,
        output_dir / "residency_policy.csv",
        output_dir / "recovery_tiers.csv",
        dependency_graph,
        recovery_scenarios,
        failover_report,
        recovery_manifest,
        validation_report,
        failback_plan,
        summary,
    ]
    checksums = _write_checksums(output_dir, files)
    return RecoveryEvidence(output_dir, validation_report, recovery_manifest, checksums)


def verify_evidence(output_dir: Path = REFERENCE_DIR) -> dict[str, Any]:
    """Verify generated recovery evidence checksums."""
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
