"""Validation result models and deterministic reports."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ValidationIssue:
    rule_id: str
    dataset: str
    record_identifier: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    datasets_validated: int
    rows_validated: int
    issues: tuple[ValidationIssue, ...]

    def write(self, output_dir: Path) -> tuple[Path, Path]:
        json_path = output_dir / "validation_report.json"
        markdown_path = output_dir / "validation_report.md"
        json_path.write_text(
            json.dumps(asdict(self), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        lines = [
            "# Synthetic data validation report",
            "",
            f"- Result: **{'PASS' if self.valid else 'FAIL'}**",
            f"- Datasets: {self.datasets_validated}",
            f"- Rows: {self.rows_validated}",
            f"- Issues: {len(self.issues)}",
            "",
        ]
        if self.issues:
            lines.extend(["## Issues", ""])
            lines.extend(
                (
                    f"- `{issue.rule_id}` `{issue.dataset}` "
                    f"`{issue.record_identifier}` — {issue.message}"
                )
                for issue in self.issues
            )
            lines.append("")
        else:
            lines.extend(
                ["All structural, referential, temporal and business-rule checks passed.", ""]
            )
        markdown_path.write_text("\n".join(lines), encoding="utf-8")
        return json_path, markdown_path
