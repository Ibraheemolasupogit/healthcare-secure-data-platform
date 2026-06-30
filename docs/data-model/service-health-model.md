# Service health model

The service health model uses controlled states:

- `HEALTHY`
- `DEGRADED`
- `UNHEALTHY`
- `UNKNOWN`
- `MAINTENANCE`
- `NOT_APPLICABLE`

Precedence is deterministic: `UNHEALTHY` outranks `DEGRADED`, which outranks
`UNKNOWN`, then `MAINTENANCE`, `HEALTHY` and `NOT_APPLICABLE`.

Inputs include dependency availability, freshness, data quality, contract
status, job status, control status, drift status, evidence integrity and
recovery readiness. These inputs are local metadata signals only.
