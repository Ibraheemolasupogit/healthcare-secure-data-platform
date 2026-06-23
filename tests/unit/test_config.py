from typing import Any

from healthcare_platform.config import load_settings, snowflake_credentials_present


def test_defaults(monkeypatch: Any) -> None:
    for name in (
        "HEALTHCARE_PLATFORM_ENV",
        "HEALTHCARE_PLATFORM_EXECUTION_MODE",
        "HEALTHCARE_PLATFORM_LOG_LEVEL",
    ):
        monkeypatch.delenv(name, raising=False)
    assert load_settings().environment == "local"


def test_credentials_require_auth(monkeypatch: Any) -> None:
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "example")
    monkeypatch.setenv("SNOWFLAKE_USER", "example")
    monkeypatch.delenv("SNOWFLAKE_PASSWORD", raising=False)
    monkeypatch.delenv("SNOWFLAKE_PRIVATE_KEY_PATH", raising=False)
    assert snowflake_credentials_present() is False
