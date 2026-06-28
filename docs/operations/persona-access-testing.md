# Persona access testing

Persona fixtures validate expected allow/deny decisions for clinical analysts, billing
analysts, finance analysts, revenue-assurance analysts, data scientists, research
analysts, report viewers, auditors and service identities.

Generate evidence with:

```bash
PYTHONPATH=src python -m healthcare_platform.cli governance generate-evidence --overwrite
```
