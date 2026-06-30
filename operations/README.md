# Operations readiness

Milestone 17 adds a repository-managed operational-readiness layer for local
observability contracts, incident readiness and recovery-drill simulation.

This area is intentionally metadata-first and credential-free. It does not
deploy monitoring infrastructure, create live alerts, open tickets, page
on-call teams, call cloud APIs or enforce production SLOs.

## Contents

- `registry/operational_controls.yaml` is the source of truth for services,
  health checks, SLIs, synthetic SLO targets, incident taxonomy, routes,
  runbooks and recovery drills.
- `validation/operations_validation_rules.yaml` documents static guardrails.
- `reference/` contains deterministic generated evidence, simulations and
  checksums.

## Local commands

```bash
healthcare-platform operations validate-registry
healthcare-platform operations evaluate-health
healthcare-platform operations simulate-incident
healthcare-platform operations simulate-drill
healthcare-platform operations generate-evidence --output-dir operations/reference --overwrite
healthcare-platform operations verify-evidence --output-dir operations/reference
```

## Boundary

All outputs are synthetic local simulations. Live SIEM, PagerDuty, Slack,
Teams, email, ServiceNow, cloud monitoring, dashboards, production runbook
automation, automatic remediation, live failover and production SLO claims are
outside this milestone.
