# Operational evidence

Generate and verify evidence:

```bash
healthcare-platform operations generate-evidence --output-dir operations/reference --overwrite
healthcare-platform operations verify-evidence --output-dir operations/reference
```

The evidence bundle includes service, health-check, SLI, SLO, taxonomy, routing,
runbook and drill catalogues plus health, incident and drill simulation reports.
Checksums are deterministic.
