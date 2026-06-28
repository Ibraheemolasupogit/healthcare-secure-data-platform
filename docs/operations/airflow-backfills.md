# Airflow backfills

Backfills are safe only when output paths are isolated by logical date or an explicit batch identifier.

Milestone 10 defaults:

- catchup is disabled;
- max active runs is one;
- reference date defaults to `2025-01-01`;
- seed defaults to `42`;
- large generation is disabled;
- overwrite is disabled unless explicitly requested.

For a backfill, set a deliberate logical date range, keep outputs under `outputs/orchestration/<workflow>/<logical-date>`, and verify checksums before using downstream results.
