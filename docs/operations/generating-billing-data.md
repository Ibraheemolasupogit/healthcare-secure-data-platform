# Generating billing data

Billing records are generated through the existing synthetic generator:

```bash
healthcare-platform generate --profile small --seed 42 \
  --reference-date 2025-01-01 --output-dir data/generated/small
```

The `--include billing` option is accepted as a source-family hint while preserving the canonical full portfolio output:

```bash
healthcare-platform generate --include billing --profile small \
  --output-dir /tmp/billing-review --overwrite
```

The committed positive sample is `data/samples/small`. It includes CSV, JSON Lines, manifest, schema catalogue, checksums and validation reports for all canonical source datasets, including billing.

