# Multi-region resilience and recovery foundation

Milestone 16 defines a repository-managed resilience and disaster-recovery design for the
synthetic healthcare platform.

The implementation is local, deterministic and simulated. It defines symbolic regions,
residency rules, recovery tiers, dependency order, platform recovery mappings, failover
criteria, failback requirements, recovery manifests and evidence. It does not deploy live
multi-region infrastructure, perform Snowflake replication, run cloud failover, move
production data or claim operational resilience certification.

## Contents

- `registry/recovery_controls.yaml` is the authoritative recovery-control registry.
- `reference/` contains generated deterministic recovery evidence.
- `validation/` documents static validation rules.

Use:

```bash
PYTHONPATH=src python -m healthcare_platform.cli recovery validate-registry
PYTHONPATH=src python -m healthcare_platform.cli recovery simulate-failover
PYTHONPATH=src python -m healthcare_platform.cli recovery generate-evidence --overwrite
PYTHONPATH=src python -m healthcare_platform.cli recovery verify-evidence
```

