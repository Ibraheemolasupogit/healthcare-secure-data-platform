"""Milestone 18 portfolio integration and release-readiness tests."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from healthcare_platform.portfolio import (
    build_portfolio_evidence,
    run_golden_path,
    show_capabilities,
    validate_portfolio,
    verify_evidence,
)
from healthcare_platform.portfolio.reference import (
    CAPABILITY_STATUSES,
    READINESS_STATUSES,
    RELEASE_STATUSES,
    golden_path_steps,
    milestone_evidence_index,
    ownership_matrix,
    technology_matrix,
)


def test_portfolio_validation_passes_with_expected_counts() -> None:
    report = validate_portfolio()

    assert report["valid"], report["errors"]
    assert report["capability_count"] == 15
    assert report["technology_count"] == 15
    assert report["ownership_domain_count"] == 16
    assert report["milestones_indexed"] == 18
    assert report["connected_service_status"] == "NOT_CONNECTED"
    assert report["deployment_status"] == "NOT_DEPLOYED"
    assert report["release_status"] == "PORTFOLIO_RELEASE_READY_WITH_LIMITATIONS"


def test_golden_path_steps_are_ordered_credential_free_and_complete() -> None:
    steps = golden_path_steps()

    assert [int(step["step"]) for step in steps] == list(range(1, 21))
    assert steps[0]["step_id"] == "verify_synthetic_sources"
    assert steps[-1]["step_id"] == "verify_final_checksums"
    assert all(step["requires_credentials"] == "false" for step in steps)
    assert {step["component"] for step in steps} >= {
        "synthetic",
        "interoperability",
        "snowflake",
        "dbt",
        "dataiku",
        "feature_store",
        "powerbi",
        "governance",
        "deployment",
        "recovery",
        "operations",
        "portfolio",
    }


def test_golden_path_execution_is_deterministic_and_not_live() -> None:
    result = run_golden_path()

    assert result["run_id"] == "GOLDEN-PATH-LOCAL-V1"
    assert result["steps_passed"] == 20
    assert result["steps_failed"] == 0
    assert result["final_readiness_status"] in READINESS_STATUSES
    assert result["final_readiness_status"] == "READY_FOR_PORTFOLIO_REVIEW"
    assert result["connected_service_status"] == "NOT_CONNECTED"
    assert result["deployment_status"] == "NOT_DEPLOYED"
    assert result["simulation_status"] == "LOCAL_SIMULATION_ONLY"
    assert result["synthetic"] is True
    assert result["local"] is True


def test_capability_matrix_has_controlled_statuses_and_resolving_evidence() -> None:
    capabilities = show_capabilities()
    capability_ids = [row["capability_id"] for row in capabilities]

    assert len(capability_ids) == len(set(capability_ids))
    for row in capabilities:
        assert row["implementation_type"] in CAPABILITY_STATUSES
        assert row["owning_milestone"]
        assert row["owning_component"]
        assert row["live_connected_status"] == "not_live_connected"
        assert row["limitations"]
        if row["evidence_reference"] != "portfolio/reference/checksums.sha256":
            assert Path(row["evidence_reference"]).exists()


def test_technology_matrix_covers_required_technologies() -> None:
    technologies = {row["technology"]: row for row in technology_matrix()}

    assert {
        "Python",
        "SQL",
        "Snowflake",
        "dbt",
        "Airflow",
        "Dataiku",
        "Microsoft Fabric",
        "Power BI",
        "Terraform",
        "GitHub Actions",
        "FHIR",
        "HL7",
        "YAML",
        "JSON",
        "Docker Compose",
    } == set(technologies)
    assert all(row["live_status"] for row in technologies.values())
    assert all(row["limitations"] for row in technologies.values())


def test_ownership_matrix_has_no_conflicting_primary_ownership() -> None:
    rows = ownership_matrix()
    domains = [row["domain"] for row in rows]
    owners = [row["primary_owner"] for row in rows]

    assert len(domains) == len(set(domains))
    assert all(owner for owner in owners)
    assert any(row["domain"] == "governance" for row in rows)
    assert all("replace" not in row["owns"].lower() for row in rows)
    assert all(row["overlap_resolution"] for row in rows)


def test_evidence_index_represents_all_milestones_and_adrs_are_indexed() -> None:
    evidence = milestone_evidence_index()

    assert [int(row["milestone"]) for row in evidence] == list(range(1, 19))
    for row in evidence:
        assert row["exists"] == "true"
        if row["primary_reference"] != "portfolio/reference/checksums.sha256":
            assert Path(row["primary_reference"]).exists()

    adr_index = Path("docs/decisions/README.md").read_text(encoding="utf-8")
    for number in range(1, 25):
        assert f"{number:04d}" in adr_index


def test_claim_validation_has_no_unsupported_findings() -> None:
    report = validate_portfolio()

    assert report["claim_validation"]["valid"] is True
    assert report["claim_validation"]["findings"] == []
    combined = json.dumps(report, sort_keys=True).lower()
    forbidden = [
        "production_ready",
        "production-ready",
        "compliant",
        "certified",
        "clinically_validated",
        "multi-region deployed",
        "live monitoring enabled",
        "live alerting enabled",
    ]
    for phrase in forbidden:
        assert phrase not in combined


def test_release_manifest_and_readiness_evidence_are_complete(tmp_path: Path) -> None:
    evidence = build_portfolio_evidence(tmp_path, overwrite=True)
    manifest = json.loads((tmp_path / "release_manifest_v1.0.json").read_text(encoding="utf-8"))
    readiness = json.loads((tmp_path / "release_readiness_report.json").read_text(encoding="utf-8"))

    assert evidence.output_dir == tmp_path
    assert manifest["version"] == "v1.0-local"
    assert manifest["milestone"] == 18
    assert manifest["commit_sha"]
    assert manifest["included_milestones"] == list(range(1, 19))
    assert manifest["deployment_status"] == "NOT_DEPLOYED"
    assert manifest["connected_service_status"] == "NOT_CONNECTED"
    assert manifest["synthetic_only"] is True
    assert manifest["rollback_reference"] == "deployment/reference/rollback_plan.md"
    assert manifest["release_readiness_status"] in RELEASE_STATUSES
    assert readiness["status"] == "READY_FOR_PORTFOLIO_REVIEW"
    assert readiness["status"] in READINESS_STATUSES


def test_portfolio_evidence_outputs_and_checksums_are_deterministic(tmp_path: Path) -> None:
    build_portfolio_evidence(tmp_path, overwrite=True)
    verification = verify_evidence(tmp_path)

    expected = {
        "capability_matrix.csv",
        "technology_matrix.csv",
        "ownership_matrix.csv",
        "milestone_evidence_index.csv",
        "architecture_validation.json",
        "claim_validation_report.json",
        "golden_path_report.json",
        "release_readiness_report.json",
        "release_manifest_v1.0.json",
        "portfolio_summary.md",
        "engineering_review_guide.md",
        "demo_script.md",
        "validation_report.json",
        "validation_report.md",
        "checksums.sha256",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected
    assert verification["valid"], verification["errors"]
    assert verification["checked_files"] == len(expected) - 1

    with (tmp_path / "capability_matrix.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 15


def test_boundary_no_new_platform_or_later_milestone_claims() -> None:
    portfolio_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in Path("portfolio").rglob("*")
        if path.is_file()
    )
    docs_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in Path("docs/portfolio").rglob("*")
        if path.is_file()
    )
    combined = portfolio_text + "\n" + docs_text

    forbidden = [
        "kubernetes",
        "siem",
        "new ml use case",
        "new feature store",
        "production-ready",
        "production_ready",
        "production_released",
        "clinically validated",
        "live deployment completed",
        "milestone 19",
    ]
    for phrase in forbidden:
        assert phrase not in combined
