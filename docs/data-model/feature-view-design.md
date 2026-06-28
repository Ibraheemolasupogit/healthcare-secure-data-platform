# Feature-view design

Feature views group compatible features by entity, source lineage, time semantics and offline-store contract.

Implemented views:

- `exception_history_features_v1`;
- `reconciliation_history_features_v1`;
- `payer_history_features_v1`;
- `appointment_history_features_v1`;
- `patient_activity_features_v1`.

Snowflake offline mapping uses `CURATED.FEATURES` contracts. Local execution does not materialise Snowflake objects.
