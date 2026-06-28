# Dataiku batch scoring

Batch scoring is blueprint-only in Milestone 11.

Steps:

1. validate scoring inputs;
2. prepare scoring features;
3. score an approved model;
4. validate predictions;
5. write governed output;
6. publish scoring evidence.

The output contract is `SERVING.ML_OUTPUTS.BILLING_EXCEPTION_PRIORITY_PREDICTIONS`. No live write occurs.
