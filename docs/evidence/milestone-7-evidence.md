# Milestone 7 evidence

Milestone 7 adds deterministic billing and finance synthetic source data to the existing generator.

## Implemented inventory

- 18 new billing/finance datasets.
- Billing profile controls for payer/service/product/tariff/contract counts and lifecycle rates.
- Decimal-safe amount generation and validation.
- Positive small sample with billing manifests, schemas, checksums and validation reports.
- Separated negative billing corpus with expected validation failures.
- CLI support for billing schema listing, schema description, validation and negative generation.
- Source-boundary documentation and static Snowflake raw contract metadata.

## Validation performed

```bash
PYTHONPATH=src pytest tests/unit/test_billing_generation.py tests/unit/test_synthetic_cli.py \
  tests/unit/test_synthetic_generation.py tests/integration/test_synthetic_output.py -q
healthcare-platform generate --profile small --seed 42 --reference-date 2025-01-01 \
  --output-dir data/samples/small --overwrite
healthcare-platform generate-negative --domain billing --profile small --seed 42 \
  --reference-date 2025-01-01 --output-dir data/negative_tests/billing --overwrite
```

Current focused results:

- Billing/source focused pytest slice: 14 passed.
- Clean `data/samples/small` generation: validation PASS.
- Negative `data/negative_tests/billing` generation: validation FAIL by design with injected defects.
- Full `make validate`: passed.
- Full pytest: 69 passed with 91% coverage.
- dbt parse: passed with 44 models, 362 data tests, 23 sources and 480 macros.
- Snowflake static validation: passed with 174 declared objects.
- Docker Compose config: passed.
- Markdown local link audit: passed.
- Clean sample checksum verification: passed.
- Deterministic regeneration comparison: passed with identical checksum files.
- Sensitive-pattern scan for real card/bank terms: no matches.
- dbt compile, docs generation and source freshness: attempted locally and failed at Snowflake connection with the placeholder profile; this is expected without credentials.
- Terraform, gitleaks and markdownlint executables were not installed locally in this shell.

## Deferred

No dbt billing sources, staging, facts, dimensions, marts, semantic models, Airflow, Dataiku, feature store, Fabric, Power BI or live Snowflake loading were implemented.
