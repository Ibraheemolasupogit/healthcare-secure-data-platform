# Dataiku governed analytics blueprint

Milestone 11 implements a repository-managed Dataiku blueprint for governed analytics and machine-learning workflows.

Current project:

- `projects/healthcare_analytics` — billing exception prioritisation blueprint.
- `contracts` — static governed output contract references.
- `templates` — reusable documentation templates.
- `validation` — reserved for future Dataiku-specific validators.

The artefacts are not Dataiku exports and were not imported into a live Dataiku instance. They describe how Dataiku should consume trusted governed dbt outputs, prepare a model-specific analytical dataset, run transparent experiments, evaluate models, apply approval gates, score approved models and monitor outcomes.

Run the local reference:

```bash
PYTHONPATH=src python -m healthcare_platform.cli dataiku-reference \
  --input dataiku/projects/healthcare_analytics/reference_data/billing_exception_analytical_fixture.csv \
  --output-dir dataiku/projects/healthcare_analytics/reference_outputs \
  --overwrite
```

Dataiku does not own raw ingestion, dbt transformations, Airflow orchestration, feature-store definitions, Fabric/Power BI artefacts or production approval.

Milestone 12 integration: Dataiku consumes exact feature-store feature set `billing_exception_prioritisation_features` version `1.0.0`. Dataiku keeps model-specific preprocessing and does not duplicate reusable feature definitions.

Milestone 13 downstream consumption: Power BI may consume governed prediction-output metadata, model version, feature-set version and validation status. Power BI must not recalculate features, retrain models, redefine thresholds or reinterpret predictions as clinical decision support.
