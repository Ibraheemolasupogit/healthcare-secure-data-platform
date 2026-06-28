# Dataiku local reference execution

Run the deterministic local reference:

```bash
PYTHONPATH=src python -m healthcare_platform.cli dataiku-reference \
  --input dataiku/projects/healthcare_analytics/reference_data/billing_exception_analytical_fixture.csv \
  --output-dir dataiku/projects/healthcare_analytics/reference_outputs \
  --overwrite
```

This validates the analytical contract, applies leakage exclusions, creates deterministic temporal splits, evaluates a majority-class baseline and a transparent scorecard candidate, writes prediction samples and generates checksums.

It is not Dataiku-produced and not Snowflake-connected.
