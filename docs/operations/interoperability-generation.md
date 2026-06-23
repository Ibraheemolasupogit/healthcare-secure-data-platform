# Interoperability generation

Generate from the reviewed Milestone 2 relational sample:

```bash
healthcare-platform interoperability generate-fhir \
  --input-dir data/samples/small/relational --output-dir /tmp/fhir
healthcare-platform interoperability generate-hl7 \
  --input-dir data/samples/small/relational --output-dir /tmp/hl7
```

Outputs are deterministic for the same source, configuration, seed and reference date. Existing directories are protected unless `--overwrite` is supplied. Only synthetic local files are supported.
