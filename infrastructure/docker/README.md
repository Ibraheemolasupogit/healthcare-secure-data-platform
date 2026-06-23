# Docker development image

The single `dev` service pins Python and installs dbt Core plus credential-free validation tools. It is intentionally not an Airflow/Snowflake emulator. Future Airflow work may add an optional profile instead of burdening the default loop.
