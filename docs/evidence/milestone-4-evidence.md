# Milestone 4 evidence

## Generated and validated

- FHIR-inspired subset: 10 resource types, 18 resource files and three example bundles.
- HL7 v2.5 subset: six message types and six messages.
- Batch: 24 parsed/mapped payloads, 24 accepted, zero warnings/rejections and 20 crosswalk rows.
- Negative corpus: eight deterministic failures and eight quarantine records.
- Outputs: envelopes, crosswalk, JSON/Markdown reports, manifest and SHA-256 checksums.
- Snowflake: eight static raw/control contracts aligned to existing Milestone 3 schemas; not deployed.
- Quality: 50 tests passed with 91% total coverage; Ruff, strict mypy and all credential-free regression gates passed.

## Reproduction

```bash
healthcare-platform interoperability process-batch \
  --input-dir data/samples/small/relational \
  --output-dir /tmp/m4-a --seed 42
healthcare-platform interoperability process-batch \
  --input-dir data/samples/small/relational \
  --output-dir /tmp/m4-b --seed 42
diff -r /tmp/m4-a /tmp/m4-b
```

The full Python, YAML, SQL, dbt, Terraform, Docker, Markdown and secret gates are recorded at handoff. No dependency was added.

## Limitations

Generated, parsed, validated, mapped, quarantined and statically contracted are evidenced. No standards validator, FHIR server, MLLP endpoint, live EHR/PAS/LIMS, Snowflake load or production terminology service was used. No formal FHIR conformance or production HL7 compatibility is claimed.
