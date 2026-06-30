# Recovery drills

Run:

```bash
healthcare-platform operations simulate-drill
```

The default drill simulates a primary-region outage using local metadata. It
evaluates RTO/RPO metadata, required approvals, route selection and runbook
linkage. No cloud action or live failover is performed.
