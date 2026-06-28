# Point-in-time correctness

The feature-store retrieval rule is:

1. identify entity key;
2. identify observation timestamp;
3. resolve feature-set version;
4. use source events with event time before observation time;
5. require availability time at or before observation time;
6. apply the declared lookback window;
7. aggregate deterministically;
8. preserve feature timestamp and source lineage;
9. record freshness and missing-feature status.

The local reference validates historical training retrieval and batch scoring retrieval using this strategy.
