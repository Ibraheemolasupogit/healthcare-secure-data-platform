# Dataiku prediction output contract

Milestone 11 defines a static governed output contract for billing exception priority predictions.

Target Snowflake location: `SERVING.ML_OUTPUTS.BILLING_EXCEPTION_PRIORITY_PREDICTIONS`.

This is a contract only. No Snowflake table is deployed and no predictions are loaded.

The grain is `reconciliation_exception_key`, `model_id`, `model_version` and `prediction_reference_date`.

The contract requires model lineage, probability bounds, decision threshold, validation status, synthetic flag and created timestamp. Direct patient identifiers are prohibited.
