# Governance registry management

Registry changes require code review, owner review and validation:

```bash
PYTHONPATH=src python -m healthcare_platform.cli governance validate-registry
```

New policies must reference controlled personas, purposes, domains, masking, row/object,
export and audit policies. Live enforcement must not be claimed without external evidence.
