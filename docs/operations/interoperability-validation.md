# Interoperability validation

```bash
healthcare-platform interoperability validate-fhir \
  --input-dir data/samples/interoperability/fhir
healthcare-platform interoperability validate-hl7 \
  --input-dir data/samples/interoperability/hl7
```

Rejected corpora return non-zero. JSON and Markdown reports distinguish mapped, preserved and unmapped content plus warnings/errors. This validation is deliberately simplified and is not formal FHIR or production HL7 conformance testing.
