"""Milestone 14 governance registry, policy simulation and evidence tests."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from healthcare_platform.governance import (
    build_governance_evidence,
    evaluate_access,
    load_governance_registry,
    unsupported_claims,
    validate_registry,
    verify_evidence,
)


def _ids(items: list[dict[str, Any]], key: str) -> set[str]:
    return {str(item[key]) for item in items}


def test_governance_registry_validates_expected_catalogue_counts() -> None:
    """The central registry is valid and materially covers M14 control families."""
    report = validate_registry()

    assert report["valid"], report["errors"]
    assert report["domain_count"] >= 11
    assert report["classification_count"] >= 11
    assert report["sensitivity_count"] == 5
    assert report["persona_count"] >= 17
    assert report["purpose_count"] >= 12
    assert report["access_policy_count"] >= 10
    assert report["masking_policy_count"] >= 5
    assert report["row_policy_count"] >= 5
    assert report["object_policy_count"] >= 8
    assert report["export_policy_count"] >= 5
    assert report["retention_policy_count"] >= 9
    assert report["audit_event_count"] >= 10
    assert report["service_identity_count"] >= 7
    assert report["control_count"] >= 7


def test_access_policy_references_resolve_and_remain_static_only() -> None:
    """Access policies reference the central catalogues and do not claim live enforcement."""
    registry = load_governance_registry()
    personas = _ids(registry["personas"]["personas"], "persona_id")
    domains = _ids(registry["domains"]["domains"], "domain_id")
    purposes = _ids(registry["purposes"]["purposes"], "purpose_id")
    classifications = _ids(registry["classifications"]["classifications"], "classification_id")
    masking = _ids(registry["masking"]["masking_policies"], "masking_policy_id")
    rows = _ids(registry["row"]["row_access_policies"], "row_policy_id")
    objects = _ids(registry["object"]["object_access_policies"], "object_policy_id")
    exports = _ids(registry["export"]["export_policies"], "export_policy_id")
    audits = _ids(registry["audit"]["audit_events"], "event_id")
    policy_ids = _ids(registry["access"]["policies"], "policy_id")

    assert len(policy_ids) == len(registry["access"]["policies"])
    assert registry["access"]["default_decision"]["effect"] == "DENY"
    for policy in registry["access"]["policies"]:
        assert policy["subject"] in personas
        assert policy["domain"] in domains
        assert policy["purpose"] in purposes
        assert policy["required_classification"] in classifications
        assert policy["masking_policy_ref"] in masking
        assert policy["row_access_policy_ref"] in rows
        assert policy["object_access_policy_ref"] in objects
        assert policy["export_policy_ref"] in exports
        assert policy["audit_event_ref"] in audits
        assert policy["owner"]
        assert policy["version"]
        assert policy["effective_from"]
        assert policy["implementation_mapping"]
        assert policy["enforcement_status"] == "not_live_enforced"
        assert policy["status"] != "LIVE_ENFORCED"


def test_personas_encode_least_privilege_and_separation_of_duties() -> None:
    """Privileged and incompatible responsibilities are explicit and testable."""
    registry = load_governance_registry()
    personas = {item["persona_id"]: item for item in registry["personas"]["personas"]}
    sod_rules = registry["roles"]["incompatible_roles"]

    assert "modify_policies" in personas["AUDITOR"]["prohibited_operations"]
    assert all(not op.startswith("manage") for op in personas["AUDITOR"]["permitted_operations"])
    assert "interactive_login" in personas["SERVICE_IDENTITY"]["prohibited_operations"]
    assert personas["BREAK_GLASS_ADMIN"]["max_duration_hours"] <= 4
    assert personas["PLATFORM_ADMIN"]["privileged"] is True
    assert personas["SECURITY_ADMIN"]["privileged"] is True
    assert personas["DATA_SCIENTIST"]["privileged"] is False

    known_personas = set(personas)
    for rule in sod_rules:
        assert set(rule["roles"]).issubset(known_personas | {"BI_PLATFORM_OWNER"})
        assert rule["prohibited_combination"]


def test_policy_simulation_default_deny_deny_precedence_and_consent() -> None:
    """Local simulator returns deterministic decisions with consent-aware research denial."""
    clinical = evaluate_access(
        persona="CLINICAL_ANALYST",
        purpose="CARE_OPERATIONS",
        environment="PROD",
        domain="operational",
        object_name="healthcare_operations_semantic",
        operation="read_aggregated_data",
        sensitivity="SYNTHETIC_HEALTH_CONFIDENTIAL",
    )
    default_deny = evaluate_access(
        persona="BILLING_ANALYST",
        purpose="BILLING_OPERATIONS",
        environment="PROD",
        domain="clinical",
        object_name="core_encounter",
        operation="read_detailed_synthetic_records",
        sensitivity="SYNTHETIC_HEALTH_CONFIDENTIAL",
    )
    research_active = evaluate_access(
        persona="RESEARCH_ANALYST",
        purpose="APPROVED_RESEARCH",
        environment="TEST",
        domain="research",
        object_name="core_research_eligibility",
        operation="read_detailed_synthetic_records",
        sensitivity="RESEARCH_RESTRICTED",
        consent_state="ACTIVE",
    )
    research_withdrawn = evaluate_access(
        persona="RESEARCH_ANALYST",
        purpose="APPROVED_RESEARCH",
        environment="TEST",
        domain="research",
        object_name="core_research_eligibility",
        operation="read_detailed_synthetic_records",
        sensitivity="RESEARCH_RESTRICTED",
        consent_state="WITHDRAWN",
    )
    finance_identifier = evaluate_access(
        persona="FINANCE_ANALYST",
        purpose="FINANCIAL_CONTROL",
        environment="PROD",
        domain="clinical",
        object_name="core_patient.synthetic_nhs_number",
        operation="read_synthetic_identifiers",
        sensitivity="SYNTHETIC_DIRECT_IDENTIFIER",
    )

    assert clinical["decision"] == "ALLOW"
    assert default_deny["decision"] == "DENY"
    assert default_deny["matched_policy"] == "ap_default_deny"
    assert research_active["decision"] == "ALLOW"
    assert research_withdrawn["decision"] == "DENY"
    assert research_withdrawn["matched_policy"] == "ap_research_withdrawn_consent_deny"
    assert finance_identifier["decision"] == "DENY"
    assert finance_identifier["matched_policy"] == "ap_finance_no_direct_identifiers"


def test_consent_policies_use_governed_outputs_without_raw_exposure() -> None:
    """Consent rules are scoped to research and avoid downstream raw consent exposure."""
    registry = load_governance_registry()
    consent_policies = registry["consent"]["consent_policies"]

    assert any(policy["purpose"] == "APPROVED_RESEARCH" for policy in consent_policies)
    for policy in consent_policies:
        assert policy["raw_consent_exposure"] in {"prohibited", "prohibited_by_default"}
        assert policy["governing_models"]
    research_policy = next(
        policy for policy in consent_policies if policy["purpose"] == "APPROVED_RESEARCH"
    )
    assert "core_research_eligibility" in research_policy["governing_models"]


def test_masking_and_sensitive_field_coverage(tmp_path: Path) -> None:
    """Direct identifiers, payment references and secret metadata have masking coverage."""
    registry = load_governance_registry()
    masking_fields = {
        field for policy in registry["masking"]["masking_policies"] for field in policy["fields"]
    }

    assert {"synthetic_nhs_number", "gateway_reference"}.issubset(masking_fields)
    assert {"external_reference", "payment_attempt_id"}.issubset(masking_fields)
    assert {"credential_reference", "secret_reference"}.issubset(masking_fields)
    for policy in registry["masking"]["masking_policies"]:
        assert policy["snowflake_mapping"]
        assert policy["powerbi_ols_mapping"]
        assert policy["clear_text_personas"] or policy["strategy"] in {
            "full_redaction",
            "null_substitution",
        }

    build_governance_evidence(tmp_path, overwrite=True)
    with (tmp_path / "sensitive_field_coverage.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert all(row["covered"] == "True" for row in rows)


def test_row_object_export_retention_and_audit_controls_resolve() -> None:
    """Cross-cutting control registries are deny-by-default and evidence-ready."""
    registry = load_governance_registry()
    retention_ids = _ids(registry["retention"]["retention_policies"], "retention_policy_id")

    assert {policy["scope_key"] for policy in registry["row"]["row_access_policies"]} >= {
        "organisation_key",
        "payer_key",
        "exception_origin",
        "cohort_id",
        "environment",
    }
    for policy in registry["row"]["row_access_policies"]:
        assert policy["default_behaviour"] == "DENY"
        assert policy["null_behaviour"] == "DENY"
        assert policy["snowflake_mapping"]
        assert policy["powerbi_rls_mapping"]

    object_policy_objects = {
        protected_object
        for policy in registry["object"]["object_access_policies"]
        for protected_object in policy["objects"]
    }
    assert {"governance.reference", "snowflake.GOVERNANCE.EVIDENCE"}.issubset(object_policy_objects)

    exports = {item["export_policy_id"]: item for item in registry["export"]["export_policies"]}
    assert exports["exp_prohibited"]["allowed_personas"] == []
    assert exports["exp_prohibited"]["destination_restrictions"] == "no_export"
    assert exports["exp_restricted_detail"]["approval_requirement"] == "data_owner_and_governance"
    assert exports["exp_aggregated_only"]["aggregation_expectation"]

    for domain in registry["domains"]["domains"]:
        assert domain["retention_policy_ref"] in retention_ids
        assert domain["export_policy_ref"] in exports

    for event in registry["audit"]["audit_events"]:
        fields = set(event["required_fields"])
        assert {"timestamp", "correlation_id", "purpose", "policy_id"}.issubset(fields)
        assert {"patient_payload", "secret_value"}.issubset(event["prohibited_payloads"])
        assert event["retention_ref"] in retention_ids


def test_service_identities_have_no_interactive_or_broad_secret_access() -> None:
    """Service identities remain references only and prohibit interactive use."""
    registry = load_governance_registry()
    for service in registry["service"]["service_identities"]:
        assert service["interactive_login"] == "prohibited"
        assert service["credential_type"] != "repository_secret_value"
        assert "interactive_login" in service["prohibited_permissions"]
        assert service["service_id"].startswith("svc_")


def test_platform_mappings_cover_existing_ownership_boundaries() -> None:
    """M14 maps existing platform ownership instead of creating competing control truth."""
    registry = load_governance_registry()
    mappings = registry["platform_mappings"]

    assert mappings["snowflake"]["ownership_source"] == "Milestone 3"
    assert mappings["snowflake"]["terraform_owner"]
    assert mappings["dbt"]["coverage_scope"] == "curated_and_externally_consumed_models"
    assert mappings["airflow"]["connected_mode_default"] == "disabled"
    assert mappings["dataiku"]["live_deployment_status"] == "not_deployed"
    assert mappings["feature_store"]["online_serving_status"] == "deferred"
    assert mappings["fabric_powerbi"]["live_deployment_status"] == "not_deployed"


def test_compliance_claim_guardrail_allows_qualified_local_language() -> None:
    """Unsupported absolute claims are absent while cautious control mappings remain."""
    registry = load_governance_registry()

    assert unsupported_claims() == []
    for control in registry["controls"]["controls"]:
        assert control["frameworks"]
        assert control["limitations"]
        assert control["implementation_status"] != "LIVE_ENFORCED"


def test_evidence_generation_is_deterministic_and_checksum_verified(tmp_path: Path) -> None:
    """Evidence generation writes the expected static pack and verifies checksums."""
    evidence = build_governance_evidence(tmp_path, overwrite=True)
    verification = verify_evidence(tmp_path)

    expected_files = {
        "policy_registry.json",
        "classification_catalogue.csv",
        "persona_access_matrix.csv",
        "access_decisions.csv",
        "masking_coverage.csv",
        "row_policy_coverage.csv",
        "sensitive_field_coverage.csv",
        "platform_control_mapping.csv",
        "compliance_control_mapping.csv",
        "unsupported_claim_report.csv",
        "validation_report.json",
        "validation_report.md",
        "evidence_manifest.json",
        "checksums.sha256",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected_files
    assert evidence.output_dir == tmp_path
    assert verification["valid"], verification["errors"]
    assert verification["checked_files"] == len(expected_files) - 1

    manifest = json.loads(evidence.evidence_manifest.read_text(encoding="utf-8"))
    assert manifest["milestone"] == 14
    assert manifest["enforcement_status"] == "not_live_enforced"
    assert manifest["certification_status"] == "not_certified"
    assert manifest["legal_advice"] == "not_provided"
    assert manifest["validation_valid"] is True


def test_boundary_static_guardrails_find_no_real_identities_or_later_scope() -> None:
    """Registry text stays synthetic, local and within M14 scope."""
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in Path("governance").rglob("*")
        if path.is_file()
    )

    assert "@example." not in text
    assert "tenant_id:" not in text
    assert "connection_string" not in text
    assert "multi-region" not in text
    assert "siem deployment" not in text
    assert "siem implementation" not in text
    assert "production dlp" not in text

    registry = load_governance_registry()
    assert all(
        policy["enforcement_status"] != "LIVE_ENFORCED" for policy in registry["access"]["policies"]
    )
    assert all(
        control["implementation_status"] != "LIVE_ENFORCED"
        for control in registry["controls"]["controls"]
    )
