# Protected CI/CD and deployment-control foundation

Milestone 15 defines the repository-managed CI/CD, promotion and deployment-control
foundation for the synthetic healthcare data platform.

The implementation is local, credential-free and statically validated. It defines
release metadata, deployment manifests, promotion gates, Terraform plan/apply boundaries,
drift simulation and rollback controls. It does not perform live Terraform apply, cloud
deployment, GitHub environment administration or production rollback.

## Contents

- `registry/deployment_controls.yaml` is the authoritative deployment-control registry.
- `reference/` contains deterministic generated release/deployment evidence.

Use:

```bash
PYTHONPATH=src python -m healthcare_platform.cli deployment validate
PYTHONPATH=src python -m healthcare_platform.cli deployment generate-evidence --overwrite
PYTHONPATH=src python -m healthcare_platform.cli deployment verify-evidence
```

