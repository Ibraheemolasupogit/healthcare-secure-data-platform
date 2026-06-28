"""Milestone 13 Fabric and Power BI consumption-layer guardrails."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from healthcare_platform.powerbi import (
    build_reference_outputs,
    load_powerbi_metadata,
    validate_model,
    verify_reference_outputs,
)


def test_powerbi_model_validates() -> None:
    result = validate_model()
    assert result["valid"], result["errors"]
    assert result["semantic_model_count"] == 1
    assert result["table_count"] >= 10
    assert result["relationship_count"] >= 10
    assert result["measure_count"] >= 12
    assert result["kpi_count"] >= 4
    assert result["report_count"] == 4
    assert result["security_role_count"] >= 5
    assert result["ols_rule_count"] >= 4


def test_tables_use_governed_sources_and_document_grain_security_and_lineage() -> None:
    metadata = load_powerbi_metadata()
    tables = metadata["model"]["tables"]
    prohibited = ("raw", "quarantine", "fhir", "hl7", "generator")
    for table in tables:
        assert all(term not in table["source_model"].lower() for term in prohibited)
        assert table["grain"]
        assert table["primary_key"]
        assert table["sensitivity"]
        assert table["owner"]
        assert table["lineage"]
        assert table["storage_mode"] == "Import"


def test_relationships_are_explicit_single_direction_and_non_ambiguous() -> None:
    metadata = load_powerbi_metadata()
    relationships = metadata["model"]["relationships"]
    ids = [relationship["relationship_id"] for relationship in relationships]
    assert len(ids) == len(set(ids))
    for relationship in relationships:
        assert relationship["cardinality"] == "one_to_many"
        assert relationship["filter_direction"] == "single"
        assert relationship["from_table"] != relationship["to_table"]
        if relationship["active"] is False:
            assert relationship.get("inactive_reason")


def test_measures_are_centralised_and_do_not_duplicate_upstream_logic() -> None:
    metadata = load_powerbi_metadata()
    reports = metadata["reports"]["reports"]
    measures = metadata["model"]["measures"]
    measure_ids = {measure["measure_id"] for measure in measures}
    for measure in measures:
        assert measure["owner"]
        assert measure["format_string"]
        assert measure["validation_rule"]
        assert measure["prohibited_reinterpretation"]
        expression = measure["expression"]
        if "/" in expression:
            assert "DIVIDE(" in expression
        assert "priority_score" not in expression.lower()
        assert "tariff" not in expression.lower()
    for report in reports:
        assert "measures" not in report or isinstance(report["measures"], list)
        for visual in report["visuals"]:
            assert set(visual["measures"]).issubset(measure_ids)


def test_kpis_are_source_grounded_and_not_regulatory_claims() -> None:
    metadata = load_powerbi_metadata()
    measure_ids = {measure["measure_id"] for measure in metadata["model"]["measures"]}
    for kpi in metadata["model"]["kpis"]:
        assert kpi["measure"] in measure_ids
        assert kpi["synthetic_portfolio_classification"].startswith("synthetic_")
        limitations = kpi["limitations"].lower()
        assert "statutory target" not in limitations or "not a statutory target" in limitations
        assert "nhs standard" not in limitations
        assert kpi["owner"]


def test_rls_ols_and_sensitivity_are_blueprint_only_with_no_real_identities() -> None:
    metadata = load_powerbi_metadata()
    text = json.dumps(metadata, sort_keys=True)
    assert "@" not in text
    assert not re.search(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        text,
    )
    roles = metadata["model"]["security"]["rls_roles"]
    assert all("role_id" in role for role in roles)
    assert any(role["deny_by_default"] for role in roles)
    for rule in metadata["model"]["security"]["ols_rules"]:
        assert rule["access"] == "hidden"
        assert rule["sensitivity_class"].startswith("synthetic_")
    assert metadata["sensitivity"]["purview_status"] == "mapping_only_not_applied"


def test_report_specs_are_thin_accessible_and_not_deployed() -> None:
    reports = load_powerbi_metadata()["reports"]
    assert reports["thin_report_policy"]["duplicate_local_semantic_models"] == "prohibited"
    assert reports["thin_report_policy"]["power_query_transformations"] == "prohibited"
    for report in reports["reports"]:
        assert report["deployment_status"] == "not_deployed"
        assert report["implementation_status"] == "specification_only"
        assert report["export_policy"]
        assert report["sensitivity"]
        for visual in report["visuals"]:
            assert visual["accessibility_text"]
            assert visual["business_question"]


def test_fabric_blueprints_do_not_claim_live_deployment() -> None:
    metadata = load_powerbi_metadata()
    assert len(metadata["workspaces"]) == 3
    for workspace in metadata["workspaces"]:
        assert workspace["implementation_status"] == "blueprint_only"
        assert workspace["synthetic_only"] is True
        assert workspace["external_sharing_policy"] == "prohibited"
    assert metadata["deployment"]["deployment_status"] == "not_deployed"
    assert metadata["endorsement"]["repository_claims"]["power_bi_certification"] == "not_claimed"
    assert metadata["connection"]["credential_policy"]["repository_credentials"] == "prohibited"


def test_reference_outputs_are_deterministic_and_checksum_verified(tmp_path: Path) -> None:
    output_dir = tmp_path / "powerbi_reference"
    first = build_reference_outputs(output_dir, overwrite=True)
    first_hashes = first.checksums.read_text(encoding="utf-8")
    second = build_reference_outputs(output_dir, overwrite=True)
    assert second.checksums.read_text(encoding="utf-8") == first_hashes
    verification = verify_reference_outputs(output_dir)
    assert verification["valid"], verification["errors"]
    manifest = json.loads(first.semantic_model_manifest.read_text(encoding="utf-8"))
    assert manifest["published"] is False
    assert manifest["certified"] is False
    assert manifest["power_bi_desktop_validated"] is False


def test_no_future_scope_implementation_or_power_bi_binary_files() -> None:
    forbidden_suffixes = {".pbix", ".pbit"}
    repo_files = [path for path in Path(".").rglob("*") if path.is_file()]
    assert not [path for path in repo_files if path.suffix.lower() in forbidden_suffixes]
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            Path("powerbi/semantic_models/healthcare_enterprise/model.yaml"),
            Path("powerbi/reports/report_portfolio.yaml"),
            Path("fabric/deployment/pipeline_blueprint.yaml"),
        ]
    ).lower()
    assert "online feature serving" not in text
    assert "fabric notebook" not in text
    assert "real-time intelligence" not in text


def test_declared_docs_and_contract_files_exist() -> None:
    expected_paths = [
        "fabric/README.md",
        "powerbi/README.md",
        "powerbi/contracts/consumption_contracts.yaml",
        "powerbi/semantic_models/healthcare_enterprise/model.yaml",
        "powerbi/reports/report_portfolio.yaml",
        "docs/decisions/0019-governed-fabric-powerbi-consumption.md",
        "docs/evidence/milestone-13-evidence.md",
    ]
    for path in expected_paths:
        assert Path(path).exists(), path
    assert yaml.safe_load(Path("powerbi/contracts/consumption_contracts.yaml").read_text())[
        "prohibited_transformations"
    ]
