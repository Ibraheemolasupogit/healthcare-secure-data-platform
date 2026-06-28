# Dataiku analytics and MLOps architecture

Milestone 11 adds a repository-managed Dataiku blueprint for governed analytics and machine-learning workflows.

Dataiku consumes trusted governed outputs produced by dbt and coordinated by Airflow. It owns collaborative analytical preparation, model-specific feature engineering, reproducible experiments, evaluation, model documentation, approval gates, scenario blueprints, batch-scoring design and model-monitoring design.

Dataiku does not own raw ingestion, canonical healthcare modelling, billing calculations, reconciliation logic, Airflow orchestration, feature-store definitions, Fabric semantic models or BI reporting.

The selected primary use case is billing exception prioritisation: estimating whether an open governed billing or reconciliation exception may require material remediation and earlier human review.

No live Dataiku instance, Dataiku API call, Snowflake connection, production deployment or model-registry publication is performed.
