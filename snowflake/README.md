# Snowflake deployment foundation

SQL is organised by concern and numbered in intended deployment order within each concern. Milestone 1 files are reviewed design scaffolds; they are not a complete deployment and contain no account identifiers. Terraform will ultimately drive durable resources, while SQL remains useful for policy definitions, review and focused validation.

Target order: account settings → databases/schemas → warehouses/monitors → ownership and functional roles/grants → security policies → ingestion → Streams/Tasks → sharing → monitoring. Scripts should be idempotent where Snowflake permits, parameterised by environment, tagged with owner/classification, and executed by a narrowly scoped deployment role.

Time Travel retention will be risk- and cost-based by layer. Temporary zero-copy clones require owner, expiry and cleanup. Secure sharing exposes approved secure views only. Future scripts must accompany positive and negative access tests.
