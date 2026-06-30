"""Local operational-readiness registry validation, simulation and evidence."""

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

REGISTRY_PATH = Path("operations/registry/operational_controls.yaml")
REFERENCE_DIR = Path("operations/reference")
LOCAL_TIMESTAMP = "2026-06-30T00:00:00Z"


@dataclass(frozen=True)
class OperationsEvidence:
    """Generated operational evidence paths."""

    output_dir: Path
    validation_report: Path
    health_report: Path
    incident_simulation: Path
    drill_simulation: Path
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


def _write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _ids(items: list[dict[str, Any]], key: str) -> set[str]:
    return {str(item[key]) for item in items}


def load_operations_registry() -> dict[str, Any]:
    """Load the central operational-readiness registry."""
    return _read_yaml(REGISTRY_PATH)


def _governance_audit_event_ids() -> set[str]:
    registry = _read_yaml(Path("governance/registry/audit_events.yaml"))
    return _ids(cast(list[dict[str, Any]], registry["audit_events"]), "event_id")


def _recovery_tier_ids() -> set[str]:
    registry = _read_yaml(Path("recovery/registry/recovery_controls.yaml"))
    return _ids(cast(list[dict[str, Any]], registry["recovery_tiers"]), "tier_id")


def _recovery_scenario_ids() -> set[str]:
    registry = _read_yaml(Path("recovery/registry/recovery_controls.yaml"))
    return _ids(cast(list[dict[str, Any]], registry["recovery_scenarios"]), "scenario_id")


def _route_for(registry: dict[str, Any], category: str, severity: str) -> dict[str, Any] | None:
    routes = cast(list[dict[str, Any]], registry["alert_routes"])
    for route in routes:
        if route["incident_type"] == category and route["severity"] == severity:
            return route
    for route in routes:
        if route["incident_type"] == category:
            return route
    return None


def _service_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(service["service_id"]): service
        for service in cast(list[dict[str, Any]], registry["services"])
    }


def _check_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(check["check_id"]): check
        for check in cast(list[dict[str, Any]], registry["health_checks"])
    }


def _runbook_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(runbook["runbook_id"]): runbook
        for runbook in cast(list[dict[str, Any]], registry["runbooks"])
    }


def _drill_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(drill["drill_id"]): drill for drill in cast(list[dict[str, Any]], registry["drills"])
    }


def _controlled_states(registry: dict[str, Any]) -> set[str]:
    return set(cast(list[str], registry["health_model"]["states"]))


def _precedence(registry: dict[str, Any]) -> dict[str, int]:
    states = cast(list[str], registry["health_model"]["precedence"])
    return {state: index for index, state in enumerate(states)}


def _worst_state(states: list[str], registry: dict[str, Any]) -> str:
    precedence = _precedence(registry)
    return min(states, key=lambda state: precedence[state])


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
        raise ValueError("operations dependency graph contains a cycle")
    return ordered


def _dependency_edges(registry: dict[str, Any]) -> list[list[str]]:
    edges: list[list[str]] = []
    for service in cast(list[dict[str, Any]], registry["services"]):
        service_id = str(service["service_id"])
        for dependency in cast(list[str], service["dependencies"]):
            edges.append([dependency, service_id])
    return edges


def _service_order(registry: dict[str, Any]) -> list[str]:
    services = sorted(_service_map(registry))
    return _topological_order(services, _dependency_edges(registry))


def _calculate_error_budget(slo: dict[str, Any]) -> dict[str, Any]:
    target = float(slo["target"])
    allowed = round(100.0 - target, 4)
    consumed = 0.0
    return {
        "slo_id": slo["slo_id"],
        "target": target,
        "allowed_failure_budget": allowed,
        "consumed_budget": consumed,
        "remaining_budget": allowed - consumed,
        "evaluation_window": slo["window"],
        "breach_status": "within_budget",
        "enforcement_status": "metadata_only",
    }


def evaluate_health(failed_checks: list[str] | None = None) -> dict[str, Any]:
    """Evaluate deterministic local service health from registry metadata."""
    registry = load_operations_registry()
    failed = set(failed_checks or [])
    checks = _check_map(registry)
    services = _service_map(registry)
    controlled = _controlled_states(registry)
    order = _service_order(registry)
    service_states: dict[str, str] = {}
    check_states: list[dict[str, Any]] = []

    for service_id in order:
        service = services[service_id]
        own_states: list[str] = []
        for check_id in cast(list[str], service["health_checks"]):
            check = checks[check_id]
            state = str(check["failure_state"] if check_id in failed else check["baseline_state"])
            if state not in controlled:
                raise ValueError(f"uncontrolled health state: {state}")
            own_states.append(state)
            check_states.append(
                {
                    "check_id": check_id,
                    "service_id": service_id,
                    "state": state,
                    "synthetic": True,
                    "live_probe": False,
                }
            )
        dependency_states = [
            service_states[str(dependency)]
            for dependency in cast(list[str], service["dependencies"])
            if str(dependency) in service_states
        ]
        state = _worst_state(own_states or ["NOT_APPLICABLE"], registry)
        if any(dependency_state == "UNHEALTHY" for dependency_state in dependency_states) or any(
            dependency_state in {"DEGRADED", "UNKNOWN"} for dependency_state in dependency_states
        ):
            state = _worst_state([state, "DEGRADED"], registry)
        service_states[service_id] = state

    overall = _worst_state(list(service_states.values()), registry)
    return {
        "generated_at": LOCAL_TIMESTAMP,
        "overall_state": overall,
        "service_states": service_states,
        "checks": check_states,
        "failed_checks": sorted(failed),
        "state_precedence": registry["health_model"]["precedence"],
        "synthetic": True,
        "live_monitoring": False,
        "limitations": "Local deterministic health evaluation only.",
    }


def _classify_severity(registry: dict[str, Any], affected_services: list[str]) -> str:
    services = _service_map(registry)
    affected_tiers = {str(services[service]["recovery_tier"]) for service in affected_services}
    if "TIER_0_CRITICAL_CONTROL_PLANE" in affected_tiers:
        return "SEV_1_CRITICAL"
    if "TIER_1_CRITICAL_DATA_SERVICES" in affected_tiers:
        return "SEV_2_HIGH"
    if "TIER_2_ANALYTICS_AND_ASSURANCE" in affected_tiers:
        return "SEV_3_MEDIUM"
    if "TIER_3_REPORTING_AND_ML" in affected_tiers:
        return "SEV_4_LOW"
    return "SEV_5_INFORMATIONAL"


def _valid_transition(registry: dict[str, Any], start: str, end: str) -> bool:
    transitions = cast(dict[str, list[str]], registry["incident_lifecycle"]["transitions"])
    return end in transitions[start]


def simulate_incident() -> dict[str, Any]:
    """Run deterministic local incident classification and routing simulation."""
    registry = load_operations_registry()
    scenario = cast(dict[str, Any], registry["simulation_scenarios"]["incident"])
    health = evaluate_health(cast(list[str], scenario["failed_checks"]))
    affected = cast(list[str], scenario["affected_services"])
    severity = _classify_severity(registry, affected)
    route = _route_for(registry, str(scenario["category"]), severity)
    if route is None:
        raise ValueError("incident route could not be resolved")
    runbook = _runbook_map(registry)[str(route["runbook"])]
    lifecycle = ["DETECTED", "TRIAGED", "ASSIGNED", "INVESTIGATING", "MITIGATING", "MONITORING"]
    transitions_valid = all(
        _valid_transition(registry, start, end)
        for start, end in zip(lifecycle, lifecycle[1:], strict=False)
    )
    escalation_required = severity in {"SEV_1_CRITICAL", "SEV_2_HIGH", "SEV_3_MEDIUM"}
    return {
        "incident_id": "INC-SYN-20260630-001",
        "scenario_id": scenario["scenario_id"],
        "category": scenario["category"],
        "severity": severity,
        "expected_severity": scenario["expected_severity"],
        "affected_services": affected,
        "route": route,
        "runbook": runbook,
        "lifecycle_path": lifecycle,
        "lifecycle_transitions_valid": transitions_valid,
        "escalation_required": escalation_required,
        "health_snapshot": health["service_states"],
        "contains_patient_payload": False,
        "live_alert_created": False,
        "ticket_created": False,
        "synthetic": True,
        "limitations": "Local simulation only; no alert delivery or ticket creation.",
    }


def describe_drill(drill_id: str) -> dict[str, Any] | None:
    """Return a drill definition by ID."""
    return _drill_map(load_operations_registry()).get(drill_id)


def simulate_drill(drill_id: str = "drill_primary_region_outage") -> dict[str, Any]:
    """Run deterministic local recovery-drill simulation."""
    registry = load_operations_registry()
    drills = _drill_map(registry)
    if drill_id not in drills:
        raise ValueError(f"unknown operations drill: {drill_id}")
    drill = drills[drill_id]
    scenario = cast(dict[str, Any], registry["simulation_scenarios"]["drill"])
    health = evaluate_health(cast(list[str], scenario["failed_checks"]))
    runbook = _runbook_map(registry)[str(drill["expected_runbook"])]
    affected = cast(list[str], drill["services"])
    severity = _classify_severity(registry, affected)
    route = _route_for(registry, "RECOVERY_READINESS", severity) or _route_for(
        registry, "RECOVERY_READINESS", "SEV_1_CRITICAL"
    )
    if route is None:
        raise ValueError("recovery-readiness route could not be resolved")
    rto_target = int(drill["rto_target_minutes"])
    rpo_target = int(drill["rpo_target_minutes"])
    simulated_duration = int(scenario["simulated_duration_minutes"])
    recovery_point_age = int(scenario["recovery_point_age_minutes"])
    rto_met = simulated_duration <= rto_target
    rpo_met = recovery_point_age <= rpo_target
    approval_required = bool(drill["required_approvals"])
    if not rto_met or not rpo_met:
        status = "DRILL_FAILED"
    elif approval_required:
        status = "DRILL_READY_WITH_APPROVAL"
    else:
        status = "DRILL_PASSED"
    return {
        "drill_id": drill_id,
        "scenario": drill["scenario"],
        "status": status,
        "expected_status": scenario["expected_status"],
        "affected_services": affected,
        "health_snapshot": health["service_states"],
        "runbook": runbook,
        "route": route,
        "rto_target_minutes": rto_target,
        "rpo_target_minutes": rpo_target,
        "simulated_duration_minutes": simulated_duration,
        "recovery_point_age_minutes": recovery_point_age,
        "rto_met": rto_met,
        "rpo_met": rpo_met,
        "approval_required": approval_required,
        "required_approvals": drill["required_approvals"],
        "cloud_action_performed": False,
        "automatic_execution": False,
        "live_failover_executed": False,
        "synthetic": True,
        "limitations": "Local recovery-drill simulation only; no cloud action performed.",
    }


def validate_operations_registry() -> dict[str, Any]:
    """Validate operational-readiness metadata and scope boundaries."""
    registry = load_operations_registry()
    errors: list[str] = []
    warnings: list[str] = []
    service_ids = _ids(cast(list[dict[str, Any]], registry["services"]), "service_id")
    check_ids = _ids(cast(list[dict[str, Any]], registry["health_checks"]), "check_id")
    sli_ids = _ids(cast(list[dict[str, Any]], registry["slis"]), "sli_id")
    slo_ids = _ids(cast(list[dict[str, Any]], registry["slos"]), "slo_id")
    runbook_ids = _ids(cast(list[dict[str, Any]], registry["runbooks"]), "runbook_id")
    drill_ids = _ids(cast(list[dict[str, Any]], registry["drills"]), "drill_id")
    route_ids = _ids(cast(list[dict[str, Any]], registry["alert_routes"]), "route_id")

    if registry["connected_status"] != "NOT_CONNECTED":
        errors.append("connected status must remain NOT_CONNECTED")
    if registry["alerting_status"] != "DISABLED":
        errors.append("alerting status must remain DISABLED")
    if registry["production_slo_commitment"] is not False:
        errors.append("production SLO commitment must remain false")
    if registry["automatic_remediation_enabled"] is not False:
        errors.append("automatic remediation must remain disabled")
    if registry["automatic_production_drills_enabled"] is not False:
        errors.append("automatic production drills must remain disabled")
    if any(value != "disabled" for value in registry["live_integrations"].values()):
        errors.append("all live integrations must remain disabled")

    collections = [
        ("service", service_ids, registry["services"]),
        ("check", check_ids, registry["health_checks"]),
        ("sli", sli_ids, registry["slis"]),
        ("slo", slo_ids, registry["slos"]),
        ("runbook", runbook_ids, registry["runbooks"]),
        ("drill", drill_ids, registry["drills"]),
        ("route", route_ids, registry["alert_routes"]),
    ]
    for label, identifiers, values in collections:
        if len(identifiers) != len(values):
            errors.append(f"{label} IDs must be unique")

    controlled_states = _controlled_states(registry)
    if controlled_states != {
        "HEALTHY",
        "DEGRADED",
        "UNHEALTHY",
        "UNKNOWN",
        "MAINTENANCE",
        "NOT_APPLICABLE",
    }:
        errors.append("health states do not match the controlled vocabulary")
    if _worst_state(["UNKNOWN", "HEALTHY"], registry) != "UNKNOWN":
        errors.append("unknown health must not promote to healthy")

    recovery_tiers = _recovery_tier_ids()
    audit_events = _governance_audit_event_ids()
    for service in cast(list[dict[str, Any]], registry["services"]):
        service_id = str(service["service_id"])
        if not service["owner_role"] or not service["business_owner_role"]:
            errors.append(f"service {service_id} missing owner")
        if service["recovery_tier"] not in recovery_tiers:
            errors.append(f"service {service_id} references unknown recovery tier")
        if service["audit_event_ref"] not in audit_events:
            errors.append(f"service {service_id} references unknown audit event")
        for dependency in cast(list[str], service["dependencies"]):
            if dependency not in service_ids:
                errors.append(f"service {service_id} has unknown dependency {dependency}")
        for check_id in cast(list[str], service["health_checks"]):
            if check_id not in check_ids:
                errors.append(f"service {service_id} references unknown check {check_id}")
        for sli_id in cast(list[str], service["sli_refs"]):
            if sli_id not in sli_ids:
                errors.append(f"service {service_id} references unknown SLI {sli_id}")
        for slo_id in cast(list[str], service["slo_refs"]):
            if slo_id not in slo_ids:
                errors.append(f"service {service_id} references unknown SLO {slo_id}")
        for runbook_id in cast(list[str], service["runbook_refs"]):
            if runbook_id not in runbook_ids:
                errors.append(f"service {service_id} references unknown runbook {runbook_id}")
        if service["synthetic_only"] is not True:
            errors.append(f"service {service_id} must remain synthetic-only")

    for check in cast(list[dict[str, Any]], registry["health_checks"]):
        if check["service_id"] not in service_ids:
            errors.append(f"check {check['check_id']} references unknown service")
        if check["baseline_state"] not in controlled_states:
            errors.append(f"check {check['check_id']} has bad baseline state")
        if check["failure_state"] not in controlled_states:
            errors.append(f"check {check['check_id']} has bad failure state")

    for sli in cast(list[dict[str, Any]], registry["slis"]):
        if sli["service_id"] not in service_ids:
            errors.append(f"SLI {sli['sli_id']} references unknown service")
        if not sli["owner"]:
            errors.append(f"SLI {sli['sli_id']} missing owner")

    for slo in cast(list[dict[str, Any]], registry["slos"]):
        if slo["sli_ref"] not in sli_ids:
            errors.append(f"SLO {slo['slo_id']} references unknown SLI")
        if slo["synthetic_target"] is not True:
            errors.append(f"SLO {slo['slo_id']} must be synthetic")
        if float(slo["warning_threshold"]) < float(slo["failure_threshold"]):
            errors.append(f"SLO {slo['slo_id']} warning threshold below failure threshold")
        if (
            "production" in str(slo["limitations"]).lower()
            and "not" not in str(slo["limitations"]).lower()
        ):
            errors.append(f"SLO {slo['slo_id']} may imply production commitment")

    for route in cast(list[dict[str, Any]], registry["alert_routes"]):
        if route["incident_type"] not in registry["incident_categories"]:
            errors.append(f"route {route['route_id']} references unknown incident type")
        if route["runbook"] not in runbook_ids:
            errors.append(f"route {route['route_id']} references unknown runbook")
        if route["audit_event"] not in audit_events:
            errors.append(f"route {route['route_id']} references unknown audit event")
        if route["notification_status"] != "disabled":
            errors.append(f"route {route['route_id']} must not enable notifications")
        if route["live_integration_status"] != "disabled":
            errors.append(f"route {route['route_id']} must not enable live integrations")

    recovery_scenarios = _recovery_scenario_ids()
    for drill in cast(list[dict[str, Any]], registry["drills"]):
        if drill["recovery_tier"] not in recovery_tiers:
            errors.append(f"drill {drill['drill_id']} references unknown recovery tier")
        if drill["expected_runbook"] not in runbook_ids:
            errors.append(f"drill {drill['drill_id']} references unknown runbook")
        if not drill["required_approvals"]:
            errors.append(f"drill {drill['drill_id']} must require approval")
        if drill["schedule_metadata"]["automatic_execution"] is not False:
            errors.append(f"drill {drill['drill_id']} must not execute automatically")
        if drill["scenario"] not in recovery_scenarios and not str(drill["scenario"]).strip():
            errors.append(f"drill {drill['drill_id']} has invalid scenario")
        for service_id in cast(list[str], drill["services"]):
            if service_id not in service_ids:
                errors.append(f"drill {drill['drill_id']} references unknown service")

    try:
        _service_order(registry)
    except ValueError as error:
        errors.append(str(error))

    health = evaluate_health()
    if health["overall_state"] != "HEALTHY":
        errors.append("baseline health evaluation must be HEALTHY")
    incident = simulate_incident()
    if incident["contains_patient_payload"]:
        errors.append("incident evidence must not contain patient payload")
    drill = simulate_drill()
    if drill["cloud_action_performed"] or drill["automatic_execution"]:
        errors.append("drill simulation must not call cloud services or execute automatically")

    serialized = json.dumps(registry, sort_keys=True).lower()
    claim_patterns = _read_yaml(Path("operations/validation/operations_validation_rules.yaml"))[
        "unsupported_claim_patterns"
    ]
    for pattern in cast(list[str], claim_patterns):
        if pattern in serialized:
            errors.append(f"unsupported operational claim detected: {pattern}")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "service_count": len(service_ids),
        "health_check_count": len(check_ids),
        "sli_count": len(sli_ids),
        "slo_count": len(slo_ids),
        "incident_category_count": len(registry["incident_categories"]),
        "route_count": len(route_ids),
        "runbook_count": len(runbook_ids),
        "drill_count": len(drill_ids),
        "connected_status": registry["connected_status"],
        "alerting_status": registry["alerting_status"],
        "monitoring_status": registry["monitoring_status"],
    }


def _validation_markdown(report: dict[str, Any]) -> str:
    status = "PASS" if report["valid"] else "FAIL"
    lines = [
        "# Operations Validation Report",
        "",
        f"- Status: {status}",
        f"- Generated at: {LOCAL_TIMESTAMP}",
        f"- Services: {report['service_count']}",
        f"- Health checks: {report['health_check_count']}",
        f"- SLIs: {report['sli_count']}",
        f"- SLOs: {report['slo_count']}",
        f"- Runbooks: {report['runbook_count']}",
        f"- Drills: {report['drill_count']}",
        "- Synthetic: true",
        "- Live monitoring: false",
        "- Live alerting: false",
        "- Production SLO commitment: false",
        "",
        "## Errors",
        "",
    ]
    lines.extend([f"- {error}" for error in report["errors"]] or ["- None"])
    lines.append("")
    return "\n".join(lines)


def _post_incident_review() -> str:
    return "\n".join(
        [
            "# Synthetic Post-Incident Review",
            "",
            "- Incident ID: INC-SYN-20260630-001",
            "- Summary: Governance checksum mismatch detected in local simulation.",
            "- Timeline: DETECTED -> TRIAGED -> ASSIGNED -> INVESTIGATING -> MITIGATING.",
            "- Impact: Control-plane metadata marked unhealthy; no live system affected.",
            "- Detection: Deterministic local health-check failure.",
            "- Response: Route to DATA_GOVERNANCE and SECURITY_OPERATIONS.",
            "- Root cause: Synthetic checksum mismatch fixture.",
            "- Contributing factors: None; this is a controlled local scenario.",
            "- Recovery actions: Regenerate trusted governance evidence.",
            "- Control failures: Evidence integrity check failed by design.",
            "- Evidence: operations/reference/incident_simulation.json.",
            "- Lessons: Control-plane checksum failures must fail closed.",
            "- Corrective actions: Verify checksum manifests before promotion.",
            "- Owners: DATA_GOVERNANCE_STEWARD, SECURITY_ADMIN.",
            "- Due dates: Review in next synthetic drill window.",
            "- Residual risk: Accepted for local simulation only.",
            "- Recurrence prevention: Keep checksum validation in CI.",
            "- Governance review: Required before closure.",
            "- Closure status: SYNTHETIC_REVIEW_OPEN.",
            "",
            "No patient payload, real identity, credential, live alert or ticket is included.",
            "",
        ]
    )


def _manifest(registry: dict[str, Any], files: list[Path]) -> dict[str, Any]:
    return {
        "generated_at": LOCAL_TIMESTAMP,
        "git_commit": _git_commit_sha(),
        "milestone": registry["milestone"],
        "synthetic": True,
        "local_simulation": True,
        "live_monitoring": False,
        "live_alerts": False,
        "external_integrations": False,
        "production_slo_commitment": False,
        "clinical_assurance_claim": False,
        "files": [path.name for path in files],
    }


def build_operations_evidence(
    output_dir: Path = REFERENCE_DIR, *, overwrite: bool = False
) -> OperationsEvidence:
    """Generate deterministic operational-readiness evidence."""
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise ValueError(f"{output_dir} is not empty; pass --overwrite to replace outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    registry = load_operations_registry()
    validation = validate_operations_registry()
    health = evaluate_health()
    incident = simulate_incident()
    drill = simulate_drill()

    service_rows = cast(list[dict[str, Any]], registry["services"])
    check_rows = cast(list[dict[str, Any]], registry["health_checks"])
    sli_rows = cast(list[dict[str, Any]], registry["slis"])
    slo_rows = cast(list[dict[str, Any]], registry["slos"])
    route_rows = cast(list[dict[str, Any]], registry["alert_routes"])
    runbook_rows = cast(list[dict[str, Any]], registry["runbooks"])

    _write_json(output_dir / "service_registry.json", service_rows)
    _write_csv(
        output_dir / "health_check_catalogue.csv",
        check_rows,
        ["check_id", "service_id", "input_type", "baseline_state", "failure_state", "source_ref"],
    )
    _write_csv(
        output_dir / "sli_catalogue.csv",
        sli_rows,
        [
            "sli_id",
            "service_id",
            "description",
            "numerator",
            "denominator",
            "unit",
            "calculation_window",
            "data_source",
            "owner",
            "implementation_status",
        ],
    )
    _write_csv(
        output_dir / "slo_catalogue.csv",
        slo_rows,
        [
            "slo_id",
            "sli_ref",
            "target",
            "window",
            "warning_threshold",
            "failure_threshold",
            "owner",
            "review_cadence",
            "breach_consequence",
            "synthetic_target",
            "limitations",
        ],
    )
    _write_json(
        output_dir / "incident_taxonomy.json",
        {
            "categories": registry["incident_categories"],
            "severity_model": registry["severity_model"],
            "lifecycle": registry["incident_lifecycle"],
            "synthetic": True,
            "clinical_severity_claim": False,
        },
    )
    _write_csv(
        output_dir / "alert_routing.csv",
        route_rows,
        [
            "route_id",
            "incident_type",
            "severity",
            "primary_owner",
            "secondary_owner",
            "escalation_window",
            "approval_requirement",
            "runbook",
            "audit_event",
            "notification_status",
            "live_integration_status",
        ],
    )
    _write_csv(
        output_dir / "runbook_catalogue.csv",
        runbook_rows,
        [
            "runbook_id",
            "trigger",
            "owner",
            "containment",
            "recovery_steps",
            "validation",
            "escalation",
            "rollback",
            "evidence",
            "limitations",
            "execution_status",
        ],
    )
    _write_json(output_dir / "drill_catalogue.json", registry["drills"])
    _write_json(output_dir / "health_report.json", health)
    _write_json(output_dir / "incident_simulation.json", incident)
    _write_json(output_dir / "drill_simulation.json", drill)
    (output_dir / "post_incident_review.md").write_text(_post_incident_review(), encoding="utf-8")
    _write_json(output_dir / "validation_report.json", validation)
    (output_dir / "validation_report.md").write_text(
        _validation_markdown(validation), encoding="utf-8"
    )

    evidence_files = [
        output_dir / "service_registry.json",
        output_dir / "health_check_catalogue.csv",
        output_dir / "sli_catalogue.csv",
        output_dir / "slo_catalogue.csv",
        output_dir / "incident_taxonomy.json",
        output_dir / "alert_routing.csv",
        output_dir / "runbook_catalogue.csv",
        output_dir / "drill_catalogue.json",
        output_dir / "health_report.json",
        output_dir / "incident_simulation.json",
        output_dir / "drill_simulation.json",
        output_dir / "post_incident_review.md",
        output_dir / "validation_report.json",
        output_dir / "validation_report.md",
    ]
    _write_json(output_dir / "evidence_manifest.json", _manifest(registry, evidence_files))
    evidence_files.append(output_dir / "evidence_manifest.json")
    checksums = "\n".join(f"{_sha256(path)}  {path.name}" for path in evidence_files)
    (output_dir / "checksums.sha256").write_text(checksums + "\n", encoding="utf-8")
    return OperationsEvidence(
        output_dir=output_dir,
        validation_report=output_dir / "validation_report.json",
        health_report=output_dir / "health_report.json",
        incident_simulation=output_dir / "incident_simulation.json",
        drill_simulation=output_dir / "drill_simulation.json",
        checksums=output_dir / "checksums.sha256",
    )


def verify_evidence(output_dir: Path = REFERENCE_DIR) -> dict[str, Any]:
    """Verify generated operations evidence checksums."""
    checksum_path = output_dir / "checksums.sha256"
    errors: list[str] = []
    checked = 0
    if not checksum_path.exists():
        return {"valid": False, "errors": ["missing checksums.sha256"], "checked_files": 0}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        expected, filename = re.split(r"\s+", line.strip(), maxsplit=1)
        path = output_dir / filename
        checked += 1
        if not path.exists():
            errors.append(f"missing evidence file: {filename}")
        elif _sha256(path) != expected:
            errors.append(f"checksum mismatch: {filename}")
    return {"valid": not errors, "errors": errors, "checked_files": checked}
