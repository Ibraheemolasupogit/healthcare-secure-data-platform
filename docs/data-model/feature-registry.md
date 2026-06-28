# Feature registry

The registry lives under `feature_store/registry`.

It records entities, feature definitions, feature views, feature sets, consumers, lifecycle and quality expectations. Each feature declares source model, source columns, event time, availability time, aggregation, lookback window, freshness, missing-value policy, owner, version and consumers.

The initial registry contains 8 reusable features, 5 feature views and 2 feature sets.
