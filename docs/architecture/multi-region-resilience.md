# Multi-region resilience architecture

Milestone 16 defines a symbolic active/passive warm-standby recovery model using
`PRIMARY_REGION`, `RECOVERY_REGION` and `ARCHIVAL_REGION`.

The design is repository-managed and synthetic-only. It documents regional roles,
residency constraints, recovery tiers, dependency order, platform recovery mappings,
failover criteria and failback requirements. It does not deploy secondary-region
infrastructure, configure Snowflake replication, move production data or claim live
resilience readiness.

