"""Safe environment-based configuration for local foundation tooling."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Non-secret runtime settings."""

    environment: str = "local"
    execution_mode: str = "local"
    log_level: str = "INFO"


def load_settings() -> Settings:
    """Load settings without reading or printing credential values."""
    return Settings(
        environment=os.getenv("HEALTHCARE_PLATFORM_ENV", "local"),
        execution_mode=os.getenv("HEALTHCARE_PLATFORM_EXECUTION_MODE", "local"),
        log_level=os.getenv("HEALTHCARE_PLATFORM_LOG_LEVEL", "INFO").upper(),
    )


def snowflake_credentials_present() -> bool:
    """Return whether a minimal future Snowflake credential set appears configured."""
    required = ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER")
    auth = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH") or os.getenv("SNOWFLAKE_PASSWORD")
    return all(os.getenv(name) for name in required) and bool(auth)
