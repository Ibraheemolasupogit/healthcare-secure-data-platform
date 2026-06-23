# Data layers

| Layer | Purpose | Allowed changes | Typical controls |
|---|---|---|---|
| RAW | Immutable, source-aligned payloads plus load metadata | Append/replay; no business correction | Restricted access, retention, file validation |
| STAGING | Rename, cast, standardise source codes, expose validity flags | One source relation per model | Schema/source tests and freshness |
| INTERMEDIATE | Reusable identity, encounter, pathway, normalisation and quality logic | Composable business rules | Unit/data tests and documented grain |
| CURATED | Conformed governed dimensions/facts and pseudonymised entities | Versioned interfaces | Contracts, policy tags, masking/row policy |
| MART | Purpose-specific operational, clinical, research, governance and quality products | Consumer-oriented aggregation | Ownership, SLAs, access roles |
| SEMANTIC | Stable reporting/research interfaces and dbt exposures | Measures and presentation contract | Consumption tests and change review |

Models use `stg_`, `int_`, `dim_`, `fct_`, and `mart_` prefixes as appropriate. Every published model must declare owner, description, grain, classification, allowed use and tests. RAW is never treated as a consumer interface. Pseudonymisation occurs before broad analytical access, but pseudonymised data remains sensitive.

Retention and Time Travel settings will vary by layer and recovery need. Zero-copy clones are temporary controlled environments, not an access-control shortcut.
