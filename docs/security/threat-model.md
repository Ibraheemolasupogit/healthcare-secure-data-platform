# Threat model

## Scope and assets

The target system protects direct identifiers, sensitive health facts, consent/cohort decisions, credentials, audit evidence and trusted analytical outputs. Trust boundaries include source landing, Snowflake administration, transformation, research workspaces, BI connections and export destinations.

| Threat | Preventive controls | Detection/response |
|---|---|---|
| Patient identifier disclosure | Isolated identifier vault, pseudonymisation, masking, least privilege | Access history, policy tests, incident revocation |
| Unauthorised research access | Purpose/time-bound approval, cohort row policy, deny by default | Grant review, expiry alerts, query audit |
| Excessive privileges | Role hierarchy, no direct grants, separation of duties | Automated entitlement tests and periodic review |
| Data exfiltration | Egress restrictions, controlled stages/shares, export approval | Volume/anomaly alerts and export audit |
| Insecure secrets | Secret manager, short-lived/key-pair auth, scanning | Rotation and exposure runbook |
| Accidental production data use | Synthetic-only policy, isolated environments, provenance checks | CI content checks and ingestion quarantine |
| Malicious/malformed files | Allow-listed formats, size/schema validation, quarantine, safe parsing | Load-error events and operator review |
| Audit-log tampering | Restricted ownership, immutable external retention | Missing-log alerts and reconciliation |
| Uncontrolled downstream exports | Read-only connectors, minimum fields, disclosure review | Destination inventory and access review |

Residual risks include re-identification through linkage, privileged administrator abuse, compromised downstream tools and misconfigured policies. Later milestones must perform misuse-case tests and record accepted risk owners. This document is a design assessment, not a certification.
