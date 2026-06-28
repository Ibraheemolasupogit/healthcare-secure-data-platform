# Batch feature retrieval

Batch retrieval uses the same registry definitions and point-in-time rules as historical retrieval.

The local reference writes `batch_scoring_set.csv` with feature values, timestamps, freshness status, missing-feature status, source lineage, retrieval timestamp and synthetic flag.

No online API or low-latency store is implemented.
