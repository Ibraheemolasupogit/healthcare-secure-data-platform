# Core history strategy

Milestone 6 keeps current-state conformed core models and records source effective dates where already present.

SCD Type 2 is not broadly implemented because the committed source fixtures contain current synthetic extracts rather than history streams. Candidate history-bearing concepts are documented through `valid_from`, `valid_to` and `is_current` where grounded:

- patient current record window from source creation/update fields
- organisation effective dates
- provider effective dates
- consent validity dates

dbt snapshots are deferred until a connected Snowflake target exists and source change-capture behaviour is proven.
