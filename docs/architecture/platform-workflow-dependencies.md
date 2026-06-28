# Platform workflow dependencies

Milestone 10 encodes the dependency chain as orchestration metadata rather than business logic.

```mermaid
flowchart LR
    Source["source preparation"] --> Interop["interoperability ingestion"]
    Interop --> Preflight["platform/dbt preflight"]
    Preflight --> Staging["dbt staging"]
    Staging --> Core["healthcare core"]
    Core --> Billing["billing and finance"]
    Billing --> Assurance["reconciliation assurance"]
    Assurance --> Evidence["assurance and run evidence"]
```

The authoritative dbt selector mapping is:

| Layer | Selector |
|---|---|
| staging | `path:models/staging` |
| core | `tag:core` |
| billing | `tag:billing` |
| finance | `tag:finance` |
| assurance | `tag:assurance` |

Source validation precedes transformation. Billing and finance precede assurance. Evidence generation follows assurance.
