"""Deterministic local reference utilities for the Power BI consumption layer."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

MODEL_PATH = Path("powerbi/semantic_models/healthcare_enterprise/model.yaml")
CONTRACT_PATH = Path("powerbi/contracts/consumption_contracts.yaml")
REPORT_PATH = Path("powerbi/reports/report_portfolio.yaml")
FABRIC_ROOT = Path("fabric")
DEFAULT_REFERENCE_OUTPUT = Path("powerbi/reference")

ALLOWED_SOURCE_PREFIXES = (
    "core_",
    "dim_",
    "fct_",
    "bridge_",
    "reconciliation_",
    "exception_",
    "open_",
    "high_",
    "revenue_",
    "daily_",
    "month_",
    "assurance_",
    "dataiku_",
    "deterministic_",
)
PROHIBITED_TERMS = (
    "notebook",
    "lakehouse",
    "real-time",
    "realtime",
    "online feature",
    "fabric pipeline implementation",
)
REAL_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
GUID_PATTERN = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


@dataclass(frozen=True)
class ReferenceOutputs:
    """Paths written by the local Power BI reference generator."""

    output_dir: Path
    semantic_model_manifest: Path
    table_catalogue: Path
    relationship_catalogue: Path
    measure_catalogue: Path
    kpi_catalogue: Path
    security_role_catalogue: Path
    report_catalogue: Path
    visual_catalogue: Path
    refresh_catalogue: Path
    validation_report: Path
    validation_markdown: Path
    checksums: Path


def _read_yaml(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))


def load_powerbi_metadata() -> dict[str, Any]:
    """Load all repository-owned Power BI/Fabric metadata."""
    return {
        "model": _read_yaml(MODEL_PATH),
        "contracts": _read_yaml(CONTRACT_PATH),
        "reports": _read_yaml(REPORT_PATH),
        "workspaces": [
            _read_yaml(path) for path in sorted((FABRIC_ROOT / "workspaces").glob("*.yaml"))
        ],
        "connection": _read_yaml(FABRIC_ROOT / "connections" / "snowflake_powerbi_connection.yaml"),
        "deployment": _read_yaml(FABRIC_ROOT / "deployment" / "pipeline_blueprint.yaml"),
        "endorsement": _read_yaml(FABRIC_ROOT / "governance" / "endorsement.yaml"),
        "sensitivity": _read_yaml(FABRIC_ROOT / "governance" / "sensitivity_mapping.yaml"),
    }


def _known_dbt_models() -> set[str]:
    names = {
        path.stem
        for root in (Path("dbt/models/curated"), Path("dbt/models/semantic"))
        for path in root.rglob("*.sql")
    }
    names.update({"dataiku_prediction_output_contract", "deterministic_date_dimension_spec"})
    return names


def _ids_unique(items: list[dict[str, Any]], field: str, label: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for item in items:
        item_id = item.get(field)
        if not isinstance(item_id, str) or not item_id:
            errors.append(f"{label} missing {field}")
        elif item_id in seen:
            errors.append(f"duplicate {label} id: {item_id}")
        else:
            seen.add(item_id)


def _contains_prohibited_text(value: Any) -> list[str]:
    text = json.dumps(value, sort_keys=True).lower()
    matches = [term.strip() for term in PROHIBITED_TERMS if term in text]
    if REAL_EMAIL_PATTERN.search(text):
        matches.append("real_email")
    if GUID_PATTERN.search(text):
        matches.append("tenant_or_workspace_guid")
    return sorted(set(matches))


def validate_model() -> dict[str, Any]:
    """Validate semantic model metadata without connecting to Power BI or Snowflake."""
    metadata = load_powerbi_metadata()
    model = metadata["model"]
    reports = metadata["reports"]
    contracts = metadata["contracts"]
    errors: list[str] = []
    warnings: list[str] = []

    tables = model.get("tables", [])
    relationships = model.get("relationships", [])
    measures = model.get("measures", [])
    kpis = model.get("kpis", [])
    reports_list = reports.get("reports", [])
    refresh_groups = model.get("refresh_groups", [])
    rls_roles = model.get("security", {}).get("rls_roles", [])
    ols_rules = model.get("security", {}).get("ols_rules", [])

    _ids_unique(tables, "table_id", "table", errors)
    _ids_unique(relationships, "relationship_id", "relationship", errors)
    _ids_unique(measures, "measure_id", "measure", errors)
    _ids_unique(kpis, "kpi_id", "kpi", errors)
    _ids_unique(reports_list, "report_id", "report", errors)
    _ids_unique(refresh_groups, "refresh_group_id", "refresh_group", errors)
    _ids_unique(rls_roles, "role_id", "rls_role", errors)

    known_sources = _known_dbt_models()
    table_ids = {table["table_id"] for table in tables}
    table_names = {table["display_name"] for table in tables}
    table_by_name = {table["display_name"]: table for table in tables}
    measure_ids = {measure["measure_id"] for measure in measures}
    refresh_ids = {group["refresh_group_id"] for group in refresh_groups}

    for table in tables:
        source_model = table.get("source_model")
        if source_model not in known_sources:
            errors.append(f"table {table.get('table_id')} references unknown source {source_model}")
        if not str(source_model).startswith(ALLOWED_SOURCE_PREFIXES):
            errors.append(f"table {table.get('table_id')} uses unsupported source {source_model}")
        for required in ("grain", "primary_key", "sensitivity", "owner", "storage_mode", "lineage"):
            if not table.get(required):
                errors.append(f"table {table.get('table_id')} missing {required}")
        if table.get("storage_mode") not in {"Import", "DirectQuery", "Composite", "Direct Lake"}:
            errors.append(f"table {table.get('table_id')} has invalid storage mode")
        if table.get("refresh_group") not in refresh_ids:
            errors.append(f"table {table.get('table_id')} has unresolved refresh group")

    for relationship in relationships:
        if relationship.get("from_table") not in table_ids:
            errors.append(
                f"relationship {relationship.get('relationship_id')} has unknown from_table"
            )
        if relationship.get("to_table") not in table_ids:
            errors.append(
                f"relationship {relationship.get('relationship_id')} has unknown to_table"
            )
        if relationship.get("cardinality") not in {"one_to_many", "many_to_one", "one_to_one"}:
            errors.append(
                f"relationship {relationship.get('relationship_id')} has invalid cardinality"
            )
        if relationship.get("filter_direction") != "single":
            errors.append(
                f"relationship {relationship.get('relationship_id')} is not single direction"
            )

    for measure in measures:
        for required in (
            "display_name",
            "expression",
            "source_columns",
            "domain",
            "format_string",
            "owner",
            "validation_rule",
            "prohibited_reinterpretation",
        ):
            if not measure.get(required):
                errors.append(f"measure {measure.get('measure_id')} missing {required}")
        expression = str(measure.get("expression", ""))
        if "/" in expression and "DIVIDE(" not in expression:
            errors.append(f"measure {measure.get('measure_id')} uses unsafe division")
        if any(term in expression.lower() for term in ("source_", "tariff", "priority_score")):
            warnings.append(
                f"measure {measure.get('measure_id')} should be reviewed for upstream logic"
            )

    for kpi in kpis:
        if kpi.get("measure") not in measure_ids:
            errors.append(f"kpi {kpi.get('kpi_id')} references unknown measure")
        for required in (
            "target",
            "warning_threshold",
            "critical_threshold",
            "owner",
            "synthetic_portfolio_classification",
        ):
            if required not in kpi:
                errors.append(f"kpi {kpi.get('kpi_id')} missing {required}")

    for role in rls_roles:
        if "@" in json.dumps(role):
            errors.append(f"rls role {role.get('role_id')} contains a real user-like identity")
        for filter_rule in role.get("filters", []):
            if filter_rule.get("table") not in table_names:
                errors.append(f"rls role {role.get('role_id')} references unknown table")

    for rule in ols_rules:
        object_name = str(rule.get("object", ""))
        table_name = object_name.split(".", maxsplit=1)[0]
        if table_name not in table_by_name:
            errors.append(f"ols object {object_name} references unknown table")
        if not rule.get("restricted_roles"):
            errors.append(f"ols object {object_name} has no restricted roles")

    for report in reports_list:
        if report.get("semantic_model") != model.get("semantic_model_id"):
            errors.append(f"report {report.get('report_id')} references unknown semantic model")
        if not report.get("export_policy") or not report.get("sensitivity"):
            errors.append(f"report {report.get('report_id')} missing export policy or sensitivity")
        for visual in report.get("visuals", []):
            for measure_id in visual.get("measures", []):
                if measure_id not in measure_ids:
                    errors.append(
                        f"visual {visual.get('visual_id')} references unknown measure {measure_id}"
                    )
            if not visual.get("accessibility_text"):
                errors.append(f"visual {visual.get('visual_id')} missing accessibility text")

    for contract in contracts.get("contracts", []):
        if contract.get("source_model") not in known_sources:
            errors.append(f"contract {contract.get('contract_id')} references unknown source")
        if contract.get("semantic_table") not in table_names:
            errors.append(
                f"contract {contract.get('contract_id')} references unknown semantic table"
            )

    prohibited = _contains_prohibited_text(metadata)
    if prohibited:
        errors.append(f"prohibited metadata detected: {', '.join(prohibited)}")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": sorted(set(warnings)),
        "semantic_model_count": 1,
        "table_count": len(tables),
        "relationship_count": len(relationships),
        "measure_count": len(measures),
        "kpi_count": len(kpis),
        "report_count": len(reports_list),
        "visual_count": sum(len(report.get("visuals", [])) for report in reports_list),
        "security_role_count": len(rls_roles),
        "ols_rule_count": len(ols_rules),
        "refresh_group_count": len(refresh_groups),
        "workspace_count": len(metadata["workspaces"]),
    }


def describe_measure(measure_id: str) -> dict[str, Any] | None:
    """Return one measure definition by ID."""
    for measure in load_powerbi_metadata()["model"].get("measures", []):
        if measure["measure_id"] == measure_id:
            return cast(dict[str, Any], measure)
    return None


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_checksums(output_dir: Path, files: list[Path]) -> Path:
    checksum_path = output_dir / "checksums.sha256"
    lines = [f"{_sha256(path)}  {path.name}" for path in sorted(files)]
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return checksum_path


def build_reference_outputs(
    output_dir: Path = DEFAULT_REFERENCE_OUTPUT, *, overwrite: bool = False
) -> ReferenceOutputs:
    """Write deterministic local Power BI reference metadata outputs."""
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise ValueError(f"{output_dir} already contains files; pass --overwrite")
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = load_powerbi_metadata()
    model = metadata["model"]
    reports = metadata["reports"]["reports"]
    validation = validate_model()

    manifest_path = output_dir / "semantic_model_manifest.json"
    manifest = {
        "semantic_model_id": model["semantic_model_id"],
        "version": model["version"],
        "status": "local_reference_metadata_only",
        "synthetic": True,
        "power_bi_desktop_validated": False,
        "published": False,
        "refreshed": False,
        "certified": False,
        "counts": {
            "tables": len(model["tables"]),
            "relationships": len(model["relationships"]),
            "measures": len(model["measures"]),
            "kpis": len(model["kpis"]),
            "reports": len(reports),
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    table_path = output_dir / "table_catalogue.csv"
    _write_csv(
        table_path,
        model["tables"],
        [
            "table_id",
            "display_name",
            "source_model",
            "grain",
            "primary_key",
            "sensitivity",
            "owner",
            "refresh_group",
            "storage_mode",
            "endorsement_status",
            "lineage",
        ],
    )
    relationship_path = output_dir / "relationship_catalogue.csv"
    _write_csv(
        relationship_path,
        model["relationships"],
        [
            "relationship_id",
            "from_table",
            "from_column",
            "to_table",
            "to_column",
            "cardinality",
            "filter_direction",
            "active",
        ],
    )
    measure_path = output_dir / "measure_catalogue.csv"
    _write_csv(
        measure_path,
        model["measures"],
        [
            "measure_id",
            "display_name",
            "expression",
            "domain",
            "format_string",
            "owner",
            "certification_status",
            "implementation_status",
            "validation_rule",
        ],
    )
    kpi_path = output_dir / "kpi_catalogue.csv"
    _write_csv(
        kpi_path,
        model["kpis"],
        [
            "kpi_id",
            "name",
            "measure",
            "target",
            "warning_threshold",
            "critical_threshold",
            "direction",
            "owner",
            "refresh",
            "source_model",
            "synthetic_portfolio_classification",
        ],
    )
    role_path = output_dir / "security_role_catalogue.csv"
    _write_csv(
        role_path,
        model["security"]["rls_roles"],
        ["role_id", "deny_by_default", "description"],
    )
    report_path = output_dir / "report_catalogue.csv"
    _write_csv(
        report_path,
        reports,
        [
            "report_id",
            "name",
            "purpose",
            "audience",
            "semantic_model",
            "export_policy",
            "sensitivity",
            "owner",
            "implementation_status",
            "deployment_status",
        ],
    )
    visuals = [
        {"report_id": report["report_id"], **visual}
        for report in reports
        for visual in report.get("visuals", [])
    ]
    visual_path = output_dir / "visual_catalogue.csv"
    _write_csv(
        visual_path,
        visuals,
        [
            "report_id",
            "visual_id",
            "type",
            "page",
            "title",
            "accessibility_text",
            "business_question",
        ],
    )
    refresh_path = output_dir / "refresh_catalogue.csv"
    _write_csv(
        refresh_path,
        model["refresh_groups"],
        [
            "refresh_group_id",
            "mode",
            "cadence",
            "dependency",
            "failure_handling",
            "incremental_refresh",
            "partition_key",
            "retention",
            "connected_status",
        ],
    )

    validation_path = output_dir / "validation_report.json"
    validation_path.write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown_path = output_dir / "validation_report.md"
    markdown_path.write_text(
        "\n".join(
            [
                "# Power BI local validation report",
                "",
                "- Local reference metadata only.",
                "- Synthetic only.",
                "- Not Power BI Desktop validated.",
                "- Not published, refreshed, deployed or certified.",
                f"- Valid: {validation['valid']}",
                f"- Tables: {validation['table_count']}",
                f"- Relationships: {validation['relationship_count']}",
                f"- Measures: {validation['measure_count']}",
                f"- KPIs: {validation['kpi_count']}",
                f"- Reports: {validation['report_count']}",
                f"- Visuals: {validation['visual_count']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    files = [
        manifest_path,
        table_path,
        relationship_path,
        measure_path,
        kpi_path,
        role_path,
        report_path,
        visual_path,
        refresh_path,
        validation_path,
        markdown_path,
    ]
    checksums = _write_checksums(output_dir, files)
    return ReferenceOutputs(
        output_dir=output_dir,
        semantic_model_manifest=manifest_path,
        table_catalogue=table_path,
        relationship_catalogue=relationship_path,
        measure_catalogue=measure_path,
        kpi_catalogue=kpi_path,
        security_role_catalogue=role_path,
        report_catalogue=report_path,
        visual_catalogue=visual_path,
        refresh_catalogue=refresh_path,
        validation_report=validation_path,
        validation_markdown=markdown_path,
        checksums=checksums,
    )


def verify_reference_outputs(output_dir: Path = DEFAULT_REFERENCE_OUTPUT) -> dict[str, Any]:
    """Verify local reference output checksums."""
    checksum_path = output_dir / "checksums.sha256"
    errors: list[str] = []
    if not checksum_path.exists():
        return {"valid": False, "errors": [f"missing {checksum_path}"]}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        expected, filename = line.split("  ", maxsplit=1)
        path = output_dir / filename
        if not path.exists():
            errors.append(f"missing {filename}")
        elif _sha256(path) != expected:
            errors.append(f"checksum mismatch {filename}")
    return {
        "valid": not errors,
        "errors": errors,
        "checked_files": len(checksum_path.read_text(encoding="utf-8").splitlines()),
    }
