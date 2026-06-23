# Milestone 2 evidence

## Reproduction record

- Command: `healthcare-platform generate --profile small --seed 42 --reference-date 2025-01-01 --output-dir data/samples/small --overwrite`
- Profile: `small`
- Seed: `42`
- Reference date: `2025-01-01`
- Manifest: `data/samples/small/manifest.json`
- Checksums: `data/samples/small/checksums.sha256`
- Validation: `data/samples/small/validation_report.json` and `.md`
- Formats: canonical CSV, equivalent JSON Lines, and explicitly non-conformant FHIR-inspired JSON

The manifest is the authoritative row-count/file inventory. Determinism is verified by generating a second small output with identical parameters and comparing `checksums.sha256`. Checksum verification uses `shasum -a 256 -c checksums.sha256` from the sample directory.

## Validation evidence

- Python: Ruff formatting/lint passed; strict mypy passed; 19 unit/integration tests passed with 93% coverage.
- Data: 15 datasets and 1,090 rows validated with zero issues; all 37 committed sample files remained below 500 KB each and totalled approximately 704 KB.
- Determinism: second generation matched canonical CSV, JSON Lines, FHIR-inspired files and `checksums.sha256` byte for byte.
- Checksums: all entries passed `shasum -a 256 -c checksums.sha256`.
- Regression: YAML and SQLFluff passed; dbt parsed without credentials (with the expected empty-model configuration warning); Terraform format/init/validate and Docker Compose configuration passed.
- Documentation: local markdownlint-cli2 passed.
- Security: Gitleaks 8.24.2 found no leaks; sample pattern inspection found no email, telephone, host path or credential material.
- Negative test: explicit negative generation produced one registered appointment defect; generation returned success as an expected fixture and validation returned non-zero with exactly one issue.
- Known limitation: manifest timestamp/runtime are intentionally not byte-stable; large profile is not executed and current in-memory relationship assembly is not suitable for the configured maximum.
