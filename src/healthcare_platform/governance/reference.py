"""Local governance-policy registry validation and evidence generation."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

REGISTRY_DIR = Path("governance/registry")
REFERENCE_DIR = Path("governance/reference")
STATUSES = {
    "DOCUMENTED",
    "STATICALLY_VALIDATED",
    "LOCALLY_SIMULATED",
    "DEPLOYMENT_READY",
    "PARTIALLY_ENFORCED",
    "EVIDENCE_VERIFIED",
    "NOT_IMPLEMENTED",
    "NOT_APPLICABLE",
}
OPERATIONS = {
    "read_aggregated_data",
    "read_detailed_synthetic_records",
    "read_synthetic_identifiers",
    "create_dbt_models",
    "execute_dbt",
    "execute_airflow_workflows",
    "manage_dataiku_projects",
    "train_models",
    "approve_models",
    "approve_own_model",
    "approve_own_policy_change",
    "approve_own_privileged_access",
    "manage_feature_definitions",
    "read_feature_sets",
    "publish_semantic_models",
    "public_publish",
    "certify_semantic_models",
    "certify_semantic_model",
    "certify_own_semantic_model",
    "view_finance_detail",
    "investigate_assurance_exceptions",
    "export_data",
    "export_restricted_detail",
    "administer_snowflake",
    "manage_security_policies",
    "read_audit_evidence",
    "interactive_login",
    "autonomous_clinical_decision",
    "modify_payment_source_records",
    "view_clinical_detail",
    "alter_invoice_calculations",
    "read_raw_consent_records",
    "redefine_governed_finance_calculations",
    "modify_policies",
    "permanent_access",
    "unreviewed_use",
}
UNSUPPORTED_CLAIM_PATTERNS = [
    r"\bgdpr compliant\b",
    r"\bhipaa compliant\b",
    r"\bnhs compliant\b",
    r"\bpci compliant\b",
    r"\biso certified\b",
    r"\bproduction secure\b",
    r"\bfully anonymised\b",
    r"\bclinically validated\b",
    r"\bregulatory approved\b",
    r"\baudit approved\b",
    r"\bzero trust implemented\b",
]
REAL_ID_PATTERNS = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    ),
    re.compile(r"(?i)(password|token|secret|private_key)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{8,}"),
]


@dataclass(frozen=True)
class GovernanceEvidence:
    """Generated governance evidence paths."""

    output_dir: Path
    validation_report: Path
    evidence_manifest: Path
    checksums: Path


def _read_yaml(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def load_governance_registry() -> dict[str, Any]:
    """Load all central governance registry files."""
    files = {
        "domains": "data_domains.yaml",
        "classifications": "classifications.yaml",
        "sensitivity": "sensitivity_levels.yaml",
        "personas": "personas.yaml",
        "roles": "roles.yaml",
        "purposes": "purposes.yaml",
        "consent": "consent_policies.yaml",
        "access": "access_policies.yaml",
        "masking": "masking_policies.yaml",
        "row": "row_access_policies.yaml",
        "object": "object_access_policies.yaml",
        "retention": "retention_policies.yaml",
        "export": "export_policies.yaml",
        "audit": "audit_events.yaml",
        "service": "service_identities.yaml",
        "controls": "control_mappings.yaml",
    }
    registry = {key: _read_yaml(REGISTRY_DIR / filename) for key, filename in files.items()}
    registry["platform_mappings"] = _read_yaml(Path("governance/mappings/platform_mappings.yaml"))
    return registry


def _unique(items: list[dict[str, Any]], key: str, label: str, errors: list[str]) -> set[str]:
    values: set[str] = set()
    for item in items:
        value = item.get(key)
        if not isinstance(value, str) or not value:
            errors.append(f"{label} missing {key}")
        elif value in values:
            errors.append(f"duplicate {label}: {value}")
        else:
            values.add(value)
    return values


def _all_text(paths: list[Path]) -> str:
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths)


def unsupported_claims() -> list[dict[str, str]]:
    """Return unsupported compliance/security claims in governance docs."""
    paths = list(Path("governance").rglob("*.yaml")) + list(Path("governance").rglob("*.md"))
    paths += [
        Path("docs/evidence/milestone-14-evidence.md"),
        Path("docs/architecture/enterprise-governance-security.md"),
    ]
    findings: list[dict[str, str]] = []
    for path in [p for p in paths if p.exists()]:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for pattern in UNSUPPORTED_CLAIM_PATTERNS:
            if re.search(pattern, text):
                findings.append({"path": str(path), "pattern": pattern})
    return findings


def validate_registry() -> dict[str, Any]:
    """Validate central governance metadata and boundary guardrails."""
    registry = load_governance_registry()
    errors: list[str] = []
    warnings: list[str] = []

    domain_ids = _unique(registry["domains"]["domains"], "domain_id", "domain", errors)
    classification_ids = _unique(
        registry["classifications"]["classifications"],
        "classification_id",
        "classification",
        errors,
    )
    sensitivity_ids = _unique(
        registry["sensitivity"]["sensitivity_levels"], "level_id", "sensitivity", errors
    )
    persona_ids = _unique(registry["personas"]["personas"], "persona_id", "persona", errors)
    purpose_ids = _unique(registry["purposes"]["purposes"], "purpose_id", "purpose", errors)
    masking_ids = _unique(
        registry["masking"]["masking_policies"], "masking_policy_id", "masking_policy", errors
    )
    row_ids = _unique(registry["row"]["row_access_policies"], "row_policy_id", "row_policy", errors)
    object_ids = _unique(
        registry["object"]["object_access_policies"], "object_policy_id", "object_policy", errors
    )
    export_ids = _unique(
        registry["export"]["export_policies"], "export_policy_id", "export_policy", errors
    )
    retention_ids = _unique(
        registry["retention"]["retention_policies"], "retention_policy_id", "retention", errors
    )
    audit_ids = _unique(registry["audit"]["audit_events"], "event_id", "audit_event", errors)
    service_ids = _unique(
        registry["service"]["service_identities"], "service_id", "service_identity", errors
    )
    control_ids = _unique(registry["controls"]["controls"], "control_id", "control", errors)
    access_ids = _unique(registry["access"]["policies"], "policy_id", "access_policy", errors)

    for classification in registry["classifications"]["classifications"]:
        if classification["sensitivity_level"] not in sensitivity_ids:
            errors.append(
                f"classification {classification['classification_id']} has bad sensitivity"
            )

    for domain in registry["domains"]["domains"]:
        for required in ("business_owner_role", "technical_owner_role", "data_steward_role"):
            if not domain.get(required):
                errors.append(f"domain {domain.get('domain_id')} missing {required}")
        if domain["sensitivity_baseline"] not in sensitivity_ids:
            errors.append(f"domain {domain['domain_id']} sensitivity does not resolve")
        if domain["retention_policy_ref"] not in retention_ids:
            errors.append(f"domain {domain['domain_id']} retention does not resolve")
        if domain["export_policy_ref"] not in export_ids:
            errors.append(f"domain {domain['domain_id']} export policy does not resolve")

    for persona in registry["personas"]["personas"]:
        for domain in persona.get("allowed_domains", []):
            if domain not in domain_ids and domain not in {"raw_interoperability"}:
                errors.append(f"persona {persona['persona_id']} references unknown domain {domain}")
        for operation in persona.get("permitted_operations", []) + persona.get(
            "prohibited_operations", []
        ):
            if operation not in OPERATIONS:
                errors.append(f"persona {persona['persona_id']} has unknown operation {operation}")
        if persona["persona_id"] == "AUDITOR" and any(
            op.startswith("manage") or op.startswith("create")
            for op in persona.get("permitted_operations", [])
        ):
            errors.append("AUDITOR must remain read-only")
        if persona["persona_id"] == "SERVICE_IDENTITY" and "interactive_login" not in persona.get(
            "prohibited_operations", []
        ):
            errors.append("SERVICE_IDENTITY must prohibit interactive login")
        if persona["persona_id"] == "BREAK_GLASS_ADMIN" and not persona.get("max_duration_hours"):
            errors.append("BREAK_GLASS_ADMIN must be time bounded")

    for policy in registry["access"]["policies"]:
        if policy["subject"] not in persona_ids:
            errors.append(f"policy {policy['policy_id']} subject does not resolve")
        if policy["domain"] not in domain_ids:
            errors.append(f"policy {policy['policy_id']} domain does not resolve")
        if policy["purpose"] not in purpose_ids:
            errors.append(f"policy {policy['policy_id']} purpose does not resolve")
        if policy["operation"] not in OPERATIONS:
            errors.append(f"policy {policy['policy_id']} operation is not controlled")
        if policy["effect"] not in {"ALLOW", "DENY"}:
            errors.append(f"policy {policy['policy_id']} has invalid effect")
        if policy["required_classification"] not in classification_ids:
            errors.append(f"policy {policy['policy_id']} classification does not resolve")
        if policy["masking_policy_ref"] not in masking_ids:
            errors.append(f"policy {policy['policy_id']} masking does not resolve")
        if policy["row_access_policy_ref"] not in row_ids:
            errors.append(f"policy {policy['policy_id']} row policy does not resolve")
        if policy["object_access_policy_ref"] not in object_ids:
            errors.append(f"policy {policy['policy_id']} object policy does not resolve")
        if policy["export_policy_ref"] not in export_ids:
            errors.append(f"policy {policy['policy_id']} export policy does not resolve")
        if policy["audit_event_ref"] not in audit_ids:
            errors.append(f"policy {policy['policy_id']} audit event does not resolve")
        if policy["status"] not in STATUSES:
            errors.append(f"policy {policy['policy_id']} status is invalid")
        if policy["enforcement_status"] == "LIVE_ENFORCED":
            errors.append(f"policy {policy['policy_id']} incorrectly claims live enforcement")

    for consent_policy in registry["consent"]["consent_policies"]:
        if consent_policy["purpose"] not in purpose_ids:
            errors.append(f"consent policy {consent_policy['consent_policy_id']} bad purpose")
        if consent_policy["raw_consent_exposure"] not in {
            "prohibited",
            "prohibited_by_default",
        }:
            errors.append(
                f"consent policy {consent_policy['consent_policy_id']} exposes raw consent"
            )

    for row_policy in registry["row"]["row_access_policies"]:
        if row_policy["default_behaviour"] != "DENY" or row_policy["null_behaviour"] != "DENY":
            errors.append(f"row policy {row_policy['row_policy_id']} must deny by default/null")

    for audit_event in registry["audit"]["audit_events"]:
        fields = set(audit_event.get("required_fields", []))
        if "correlation_id" not in fields or "timestamp" not in fields:
            errors.append(f"audit event {audit_event['event_id']} missing timestamp/correlation")
        if audit_event["retention_ref"] not in retention_ids:
            errors.append(f"audit event {audit_event['event_id']} retention does not resolve")
        prohibited = set(audit_event.get("prohibited_payloads", []))
        if "patient_payload" not in prohibited or "secret_value" not in prohibited:
            errors.append(f"audit event {audit_event['event_id']} must prohibit payloads/secrets")

    for service in registry["service"]["service_identities"]:
        if service["interactive_login"] != "prohibited":
            errors.append(f"service {service['service_id']} allows interactive login")

    for control in registry["controls"]["controls"]:
        if control["control_id"] not in control_ids:
            errors.append("unreachable control id")
        if control["implementation_status"] == "LIVE_ENFORCED":
            errors.append(f"control {control['control_id']} incorrectly claims live enforcement")
        if not control.get("limitations"):
            errors.append(f"control {control['control_id']} missing limitations")

    all_registry_text = _all_text(list(Path("governance").rglob("*.yaml")))
    for pattern in REAL_ID_PATTERNS:
        if pattern.search(all_registry_text):
            errors.append("real identity, tenant id, credential-like value, or secret detected")

    claims = unsupported_claims()
    if claims:
        errors.append(f"unsupported compliance claims detected: {len(claims)}")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "domain_count": len(domain_ids),
        "classification_count": len(classification_ids),
        "sensitivity_count": len(sensitivity_ids),
        "persona_count": len(persona_ids),
        "purpose_count": len(purpose_ids),
        "access_policy_count": len(access_ids),
        "masking_policy_count": len(masking_ids),
        "row_policy_count": len(row_ids),
        "object_policy_count": len(object_ids),
        "export_policy_count": len(export_ids),
        "retention_policy_count": len(retention_ids),
        "audit_event_count": len(audit_ids),
        "service_identity_count": len(service_ids),
        "control_count": len(control_ids),
    }


def describe_policy(policy_id: str) -> dict[str, Any] | None:
    """Return one access policy."""
    for policy in load_governance_registry()["access"]["policies"]:
        if policy["policy_id"] == policy_id:
            return cast(dict[str, Any], policy)
    return None


def evaluate_access(
    *,
    persona: str,
    purpose: str,
    environment: str,
    domain: str,
    object_name: str,
    operation: str,
    sensitivity: str,
    consent_state: str = "not_applicable",
    export_request: bool = False,
) -> dict[str, Any]:
    """Simulate a local governance access decision."""
    registry = load_governance_registry()
    candidates = [
        policy
        for policy in registry["access"]["policies"]
        if policy["subject"] == persona
        and policy["purpose"] == purpose
        and policy["environment"] == environment
        and policy["domain"] == domain
        and policy["operation"] == operation
        and (policy["object"] == object_name or policy["object"] in object_name)
    ]
    if consent_state not in {"WITHDRAWN", "EXPIRED"}:
        candidates = [
            policy
            for policy in candidates
            if policy["policy_id"] != "ap_research_withdrawn_consent_deny"
        ]
    if consent_state in {"WITHDRAWN", "EXPIRED"} and purpose == "APPROVED_RESEARCH":
        deny = next(
            policy
            for policy in registry["access"]["policies"]
            if policy["policy_id"] == "ap_research_withdrawn_consent_deny"
        )
        candidates = [deny]
    deny_candidates = [policy for policy in candidates if policy["effect"] == "DENY"]
    allow_candidates = [policy for policy in candidates if policy["effect"] == "ALLOW"]
    matched = (deny_candidates or allow_candidates or [registry["access"]["default_decision"]])[0]
    decision = matched["effect"]
    return {
        "decision": decision,
        "matched_policy": matched["policy_id"],
        "reason": matched.get("reason", f"matched {matched['policy_id']}"),
        "masking_policy": matched.get("masking_policy_ref"),
        "row_policy": matched.get("row_access_policy_ref"),
        "object_policy": matched.get("object_access_policy_ref"),
        "export_policy": matched.get("export_policy_ref"),
        "audit_requirement": matched.get("audit_event_ref"),
        "approval_requirement": matched.get("required_approval"),
        "policy_version": matched.get("version", registry["access"]["version"]),
        "limitations": "Local deterministic policy simulation; not production enforcement.",
        "input": {
            "persona": persona,
            "purpose": purpose,
            "environment": environment,
            "domain": domain,
            "object": object_name,
            "operation": operation,
            "sensitivity": sensitivity,
            "consent_state": consent_state,
            "export_request": export_request,
        },
    }


def _decision_fixtures() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": "clinical_aggregate_allowed",
            "persona": "CLINICAL_ANALYST",
            "purpose": "CARE_OPERATIONS",
            "environment": "PROD",
            "domain": "operational",
            "object_name": "healthcare_operations_semantic",
            "operation": "read_aggregated_data",
            "sensitivity": "SYNTHETIC_HEALTH_CONFIDENTIAL",
            "expected_decision": "ALLOW",
        },
        {
            "scenario_id": "billing_no_clinical_detail_default_deny",
            "persona": "BILLING_ANALYST",
            "purpose": "BILLING_OPERATIONS",
            "environment": "PROD",
            "domain": "clinical",
            "object_name": "core_encounter",
            "operation": "read_detailed_synthetic_records",
            "sensitivity": "SYNTHETIC_HEALTH_CONFIDENTIAL",
            "expected_decision": "DENY",
        },
        {
            "scenario_id": "finance_direct_identifier_denied",
            "persona": "FINANCE_ANALYST",
            "purpose": "FINANCIAL_CONTROL",
            "environment": "PROD",
            "domain": "clinical",
            "object_name": "core_patient.synthetic_nhs_number",
            "operation": "read_synthetic_identifiers",
            "sensitivity": "SYNTHETIC_DIRECT_IDENTIFIER",
            "expected_decision": "DENY",
        },
        {
            "scenario_id": "revenue_assurance_exception_allowed",
            "persona": "REVENUE_ASSURANCE_ANALYST",
            "purpose": "REVENUE_ASSURANCE",
            "environment": "PROD",
            "domain": "assurance",
            "object_name": "reconciliation_exception",
            "operation": "investigate_assurance_exceptions",
            "sensitivity": "SYNTHETIC_FINANCIAL_CONFIDENTIAL",
            "expected_decision": "ALLOW",
        },
        {
            "scenario_id": "research_active_consent_allowed",
            "persona": "RESEARCH_ANALYST",
            "purpose": "APPROVED_RESEARCH",
            "environment": "TEST",
            "domain": "research",
            "object_name": "core_research_eligibility",
            "operation": "read_detailed_synthetic_records",
            "sensitivity": "RESEARCH_RESTRICTED",
            "consent_state": "ACTIVE",
            "expected_decision": "ALLOW",
        },
        {
            "scenario_id": "research_withdrawn_consent_denied",
            "persona": "RESEARCH_ANALYST",
            "purpose": "APPROVED_RESEARCH",
            "environment": "TEST",
            "domain": "research",
            "object_name": "core_research_eligibility",
            "operation": "read_detailed_synthetic_records",
            "sensitivity": "RESEARCH_RESTRICTED",
            "consent_state": "WITHDRAWN",
            "expected_decision": "DENY",
        },
        {
            "scenario_id": "report_viewer_detail_export_denied",
            "persona": "REPORT_VIEWER",
            "purpose": "SERVICE_PLANNING",
            "environment": "PROD",
            "domain": "semantic_consumption",
            "object_name": "healthcare_enterprise",
            "operation": "export_restricted_detail",
            "sensitivity": "SYNTHETIC_HEALTH_CONFIDENTIAL",
            "export_request": True,
            "expected_decision": "DENY",
        },
        {
            "scenario_id": "auditor_evidence_allowed",
            "persona": "AUDITOR",
            "purpose": "SECURITY_AUDIT",
            "environment": "PROD",
            "domain": "governance_audit",
            "object_name": "governance_evidence",
            "operation": "read_audit_evidence",
            "sensitivity": "SECURITY_AUDIT",
            "expected_decision": "ALLOW",
        },
        {
            "scenario_id": "service_identity_interactive_denied",
            "persona": "SERVICE_IDENTITY",
            "purpose": "PLATFORM_ADMINISTRATION",
            "environment": "PROD",
            "domain": "governance_audit",
            "object_name": "service_identity",
            "operation": "interactive_login",
            "sensitivity": "SECRET_METADATA",
            "expected_decision": "DENY",
        },
        {
            "scenario_id": "data_scientist_feature_allowed",
            "persona": "DATA_SCIENTIST",
            "purpose": "MODEL_DEVELOPMENT",
            "environment": "TEST",
            "domain": "feature_store",
            "object_name": "billing_exception_prioritisation_features",
            "operation": "read_feature_sets",
            "sensitivity": "MODEL_GOVERNANCE",
            "expected_decision": "ALLOW",
        },
    ]


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_checksums(output_dir: Path, files: list[Path]) -> Path:
    path = output_dir / "checksums.sha256"
    path.write_text(
        "\n".join(f"{_sha256(file)}  {file.name}" for file in sorted(files)) + "\n",
        encoding="utf-8",
    )
    return path


def build_governance_evidence(
    output_dir: Path = REFERENCE_DIR, *, overwrite: bool = False
) -> GovernanceEvidence:
    """Generate deterministic local governance evidence outputs."""
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise ValueError(f"{output_dir} already contains files; pass --overwrite")
    output_dir.mkdir(parents=True, exist_ok=True)
    registry = load_governance_registry()
    validation = validate_registry()

    policy_registry = output_dir / "policy_registry.json"
    policy_registry.write_text(
        json.dumps(registry["access"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    _write_csv(
        output_dir / "classification_catalogue.csv",
        registry["classifications"]["classifications"],
        ["classification_id", "sensitivity_level", "description"],
    )
    personas = registry["personas"]["personas"]
    _write_csv(
        output_dir / "persona_access_matrix.csv",
        personas,
        [
            "persona_id",
            "allowed_domains",
            "permitted_purposes",
            "permitted_operations",
            "export_allowance",
            "privileged",
        ],
    )
    decisions = []
    for fixture in _decision_fixtures():
        decision = evaluate_access(
            persona=fixture["persona"],
            purpose=fixture["purpose"],
            environment=fixture["environment"],
            domain=fixture["domain"],
            object_name=fixture["object_name"],
            operation=fixture["operation"],
            sensitivity=fixture["sensitivity"],
            consent_state=fixture.get("consent_state", "not_applicable"),
            export_request=fixture.get("export_request", False),
        )
        decisions.append(
            {
                "scenario_id": fixture["scenario_id"],
                "persona": fixture["persona"],
                "decision": decision["decision"],
                "expected_decision": fixture["expected_decision"],
                "matched_policy": decision["matched_policy"],
                "reason": decision["reason"],
            }
        )
    _write_csv(
        output_dir / "access_decisions.csv",
        decisions,
        ["scenario_id", "persona", "decision", "expected_decision", "matched_policy", "reason"],
    )
    _write_csv(
        output_dir / "masking_coverage.csv",
        [
            {"field": field, "masking_policy_id": policy["masking_policy_id"]}
            for policy in registry["masking"]["masking_policies"]
            for field in policy["fields"]
        ],
        ["field", "masking_policy_id"],
    )
    _write_csv(
        output_dir / "row_policy_coverage.csv",
        registry["row"]["row_access_policies"],
        [
            "row_policy_id",
            "protected_object",
            "scope_key",
            "default_behaviour",
            "snowflake_mapping",
            "powerbi_rls_mapping",
        ],
    )
    sensitive_fields = [
        {"field": "synthetic_nhs_number", "classification": "SYNTHETIC_DIRECT_IDENTIFIER"},
        {"field": "patient_pseudonym", "classification": "SYNTHETIC_QUASI_IDENTIFIER"},
        {"field": "birth_date", "classification": "SYNTHETIC_QUASI_IDENTIFIER"},
        {"field": "postcode_sector", "classification": "SYNTHETIC_QUASI_IDENTIFIER"},
        {"field": "external_reference", "classification": "SYNTHETIC_FINANCIAL_CONFIDENTIAL"},
        {"field": "evidence_reference", "classification": "MODEL_GOVERNANCE"},
        {"field": "secret_reference", "classification": "SECRET_METADATA"},
    ]
    masking_fields = {
        field
        for policy in registry["masking"]["masking_policies"]
        for field in policy.get("fields", [])
    }
    _write_csv(
        output_dir / "sensitive_field_coverage.csv",
        [{**field, "covered": field["field"] in masking_fields} for field in sensitive_fields],
        ["field", "classification", "covered"],
    )
    _write_csv(
        output_dir / "platform_control_mapping.csv",
        [
            {"platform": platform, **details}
            for platform, details in registry["platform_mappings"].items()
            if isinstance(details, dict)
        ],
        ["platform", "deployment_status", "live_deployment_status", "mapped_constructs"],
    )
    _write_csv(
        output_dir / "compliance_control_mapping.csv",
        registry["controls"]["controls"],
        [
            "control_id",
            "theme",
            "frameworks",
            "implementation_status",
            "evidence_ref",
            "limitations",
        ],
    )
    _write_csv(
        output_dir / "unsupported_claim_report.csv",
        unsupported_claims(),
        ["path", "pattern"],
    )
    validation_report = output_dir / "validation_report.json"
    validation_report.write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    validation_md = output_dir / "validation_report.md"
    validation_md.write_text(
        "\n".join(
            [
                "# Governance validation report",
                "",
                "- Local deterministic governance evidence.",
                "- Synthetic portfolio only.",
                "- Simulated and statically validated; not live-enforced.",
                "- Not independently certified and not legal advice.",
                f"- Valid: {validation['valid']}",
                f"- Access policies: {validation['access_policy_count']}",
                f"- Personas: {validation['persona_count']}",
                f"- Controls: {validation['control_count']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = output_dir / "evidence_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "milestone": 14,
                "status": "local_simulated_static_evidence",
                "connected_status": {
                    "snowflake": "not_connected",
                    "entra_id": "not_connected",
                    "purview": "not_connected",
                    "dataiku": "not_connected",
                    "fabric_powerbi": "not_connected",
                },
                "enforcement_status": "not_live_enforced",
                "certification_status": "not_certified",
                "legal_advice": "not_provided",
                "validation_valid": validation["valid"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    files = [
        policy_registry,
        output_dir / "classification_catalogue.csv",
        output_dir / "persona_access_matrix.csv",
        output_dir / "access_decisions.csv",
        output_dir / "masking_coverage.csv",
        output_dir / "row_policy_coverage.csv",
        output_dir / "sensitive_field_coverage.csv",
        output_dir / "platform_control_mapping.csv",
        output_dir / "compliance_control_mapping.csv",
        output_dir / "unsupported_claim_report.csv",
        validation_report,
        validation_md,
        manifest,
    ]
    checksums = _write_checksums(output_dir, files)
    return GovernanceEvidence(output_dir, validation_report, manifest, checksums)


def verify_evidence(output_dir: Path = REFERENCE_DIR) -> dict[str, Any]:
    """Verify generated governance evidence checksums."""
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
