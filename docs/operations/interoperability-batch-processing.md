# Interoperability batch processing

```bash
healthcare-platform interoperability process-batch \
  --input-dir data/samples/small/relational \
  --output-dir /tmp/interoperability --seed 42
healthcare-platform interoperability inspect-quarantine \
  --input-dir data/negative_tests/interoperability/quarantine
healthcare-platform interoperability describe-contracts
```

Batch processing writes source payloads, envelopes, crosswalks, reports, manifest and checksums. It makes no network or Snowflake connection. The SQL preview is not executed and live loading remains excluded.
