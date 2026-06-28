# Dataiku project import

The repository contains Dataiku blueprints, not a Dataiku export.

Before importing into a real Dataiku instance:

1. Confirm Snowflake governed inputs are deployed and approved.
2. Configure a Dataiku Snowflake connection using approved secret handling.
3. Recreate the Flow from `dataiku/projects/healthcare_analytics/flow.yaml`.
4. Implement recipes from repository specifications.
5. Run checks before training.
6. Capture Dataiku-native evidence separately.

Do not claim live Dataiku execution from repository blueprints alone.
