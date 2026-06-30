# Drift report model

`deployment/reference/drift_report.json` records the local file-based drift simulation.
It compares expected and observed synthetic resource names, classifies added/removed/changed
items and assigns deterministic severity.

The report does not query live infrastructure and does not perform automatic remediation.

