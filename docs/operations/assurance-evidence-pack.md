# Assurance evidence pack runbook

Generate a deterministic local Milestone 9 evidence pack:

```bash
PYTHONPATH=src python -m healthcare_platform.cli assurance-evidence \
  --output-dir /tmp/m9-assurance-evidence --overwrite
```

The command writes:

- `assurance_evidence_manifest.json`;
- `assurance_inventory.csv`;
- `assurance_evidence_summary.md`;
- `checksums.sha256`.

The pack inventories assurance dbt models, macros and rule seeds. It does not connect to Snowflake and does not recalculate billing or finance amounts.
