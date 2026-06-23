# Generating synthetic data

Install the project, then run:

```bash
healthcare-platform generate \
  --profile small \
  --seed 42 \
  --reference-date 2025-01-01 \
  --output-dir data/generated/small
```

Use `--patient-count` for a bounded override, `--format csv|jsonl|all`, and `--overwrite` only when replacement is intended. Existing non-empty output is protected. `describe-profile small` prints configuration and row estimates; `list-datasets` prints the schema catalogue.

The reference date replaces wall-clock time in all clinical logic. The same code version, profile, configuration, seed and reference date produces equivalent canonical CSV/JSON/FHIR files and stable checksums. Manifest generation timestamp, runtime duration and Git dirty state are operational metadata and may differ.

Defects are disabled by default. To create an intentionally failing fixture:

```bash
healthcare-platform generate --profile small --patient-count 20 \
  --inject-defects --negative-test-mode \
  --output-dir data/negative_tests/small
```

Negative-test mode requires a path under `negative_tests`; every injected defect is represented in `data_quality_events`. It currently injects a cancelled appointment without a reason. Critical foreign-key corruption is not implemented.
