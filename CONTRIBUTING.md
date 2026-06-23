# Contributing

Work in milestone-sized changes. Create a short-lived branch, add or update tests and documentation, run `make validate`, and use a pull request. Keep Snowflake SQL modular and idempotent where practical; keep dbt transformations inside dbt; do not move reporting logic into BI tools.

Never commit real health data, identifiers, secrets, credentials, account locators, or generated large datasets. Use synthetic fixtures that are obviously fictional. New architecture choices should add or supersede an ADR. Claims in documentation require corresponding test or evidence.

Commits should be focused and use an imperative summary, for example `chore: establish milestone 1 foundation`. Pull requests must state scope, exclusions, validation, security impact, and rollback approach.
