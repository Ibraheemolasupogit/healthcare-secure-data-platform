# Historical feature retrieval

Build the local historical retrieval reference:

```bash
PYTHONPATH=src python -m healthcare_platform.cli feature-store build-reference \
  --output-dir feature_store/reference/outputs --overwrite
```

The output includes `historical_training_set.csv`, registry snapshots, validation report and checksums.

This is local synthetic evidence, not Snowflake materialisation.
