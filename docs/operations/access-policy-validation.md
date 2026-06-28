# Access-policy validation

Use the local simulator to inspect deterministic decisions:

```bash
PYTHONPATH=src python -m healthcare_platform.cli governance evaluate-access \
  --persona CLINICAL_ANALYST --purpose CARE_OPERATIONS --environment PROD \
  --domain operational --object healthcare_operations_semantic \
  --operation read_aggregated_data --sensitivity SYNTHETIC_HEALTH_CONFIDENTIAL
```

The simulator is not production authorisation infrastructure.
