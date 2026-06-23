from typing import Any

from healthcare_platform import cli


def test_info_is_safe(capsys: Any, monkeypatch: Any) -> None:
    monkeypatch.setattr(cli, "dbt_available", lambda: False)
    assert cli.main(["info"]) == 0
    output = capsys.readouterr().out
    assert "Healthcare Secure Data Platform" in output
    assert "snowflake_credentials_configured:" in output
    assert "dbt_available: False" in output
