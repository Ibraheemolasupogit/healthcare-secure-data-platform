# Synthetic Post-Incident Review

- Incident ID: INC-SYN-20260630-001
- Summary: Governance checksum mismatch detected in local simulation.
- Timeline: DETECTED -> TRIAGED -> ASSIGNED -> INVESTIGATING -> MITIGATING.
- Impact: Control-plane metadata marked unhealthy; no live system affected.
- Detection: Deterministic local health-check failure.
- Response: Route to DATA_GOVERNANCE and SECURITY_OPERATIONS.
- Root cause: Synthetic checksum mismatch fixture.
- Contributing factors: None; this is a controlled local scenario.
- Recovery actions: Regenerate trusted governance evidence.
- Control failures: Evidence integrity check failed by design.
- Evidence: operations/reference/incident_simulation.json.
- Lessons: Control-plane checksum failures must fail closed.
- Corrective actions: Verify checksum manifests before promotion.
- Owners: DATA_GOVERNANCE_STEWARD, SECURITY_ADMIN.
- Due dates: Review in next synthetic drill window.
- Residual risk: Accepted for local simulation only.
- Recurrence prevention: Keep checksum validation in CI.
- Governance review: Required before closure.
- Closure status: SYNTHETIC_REVIEW_OPEN.

No patient payload, real identity, credential, live alert or ticket is included.
