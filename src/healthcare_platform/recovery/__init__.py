"""Recovery registry validation and local failover simulation."""

from healthcare_platform.recovery.reference import (
    build_recovery_evidence,
    describe_scenario,
    load_recovery_registry,
    simulate_failover,
    validate_recovery_registry,
    verify_evidence,
)

__all__ = [
    "build_recovery_evidence",
    "describe_scenario",
    "load_recovery_registry",
    "simulate_failover",
    "validate_recovery_registry",
    "verify_evidence",
]
