from pathlib import Path
from typing import Any

from healthcare_platform import cli


def test_profile_and_dataset_commands(capsys: Any) -> None:
    assert cli.main(["describe-profile", "small"]) == 0
    assert '"patient_count": 100' in capsys.readouterr().out
    assert cli.main(["list-datasets"]) == 0
    assert "patients: schema 1.0.0" in capsys.readouterr().out
    assert cli.main(["list-datasets", "--domain", "billing"]) == 0
    billing_output = capsys.readouterr().out
    assert "invoices: schema 1.0.0" in billing_output
    assert "patients: schema 1.0.0" not in billing_output
    assert cli.main(["describe-schema", "invoices"]) == 0
    assert '"name": "invoices"' in capsys.readouterr().out


def test_generate_and_validate_cli(tmp_path: Path, capsys: Any) -> None:
    output = tmp_path / "sample"
    args = [
        "generate",
        "--profile",
        "small",
        "--patient-count",
        "8",
        "--seed",
        "7",
        "--reference-date",
        "2025-01-01",
        "--output-dir",
        str(output),
    ]
    assert cli.main(args) == 0
    assert "validation: PASS" in capsys.readouterr().out
    assert cli.main(args) == 2
    assert "--overwrite" in capsys.readouterr().out
    assert cli.main(["validate-data", "--input-dir", str(output)]) == 0
    assert cli.main(["validate-billing", "--input-dir", str(output)]) == 0


def test_generate_negative_billing_cli(tmp_path: Path, capsys: Any) -> None:
    output = tmp_path / "negative_tests" / "billing"
    assert (
        cli.main(
            [
                "generate-negative",
                "--domain",
                "billing",
                "--profile",
                "small",
                "--output-dir",
                str(output),
            ]
        )
        == 0
    )
    generated = capsys.readouterr().out
    assert "negative_output_dir:" in generated
    assert "billing_exceptions:" in generated
    assert "validation: FAIL" in generated
    assert cli.main(["validate-billing", "--input-dir", str(output)]) == 1
