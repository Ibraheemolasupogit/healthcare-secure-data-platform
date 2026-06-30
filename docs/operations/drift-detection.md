# Drift detection

The Milestone 15 drift check is a deterministic local simulation. It compares expected and
observed resource identifiers from the deployment registry, reports added/removed/changed
items and assigns severity.

Future live drift checks may run Terraform plans or platform metadata comparisons, but
automatic remediation remains prohibited without approval.

