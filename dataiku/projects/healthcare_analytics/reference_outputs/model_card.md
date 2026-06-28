# Billing exception prioritisation local reference model card

Status: local reference only; not Dataiku-produced, not deployed and not production-approved.

Intended use: demonstrate governed Dataiku workflow design for prioritising synthetic billing exceptions for human review.

Prohibited use: autonomous clinical decisions, patient treatment decisions, financial posting, production exception assignment or regulatory certification.

Training data: synthetic fixture representing governed Milestone 9 exception outputs.

Target: `material_remediation_required`.

Features: transparent exception attributes excluding Milestone 9 deterministic priority score and post-resolution fields.

Primary metric: F1 = `0.6667` on the local test split.

Human oversight: finance-control and data-quality roles must review any prioritisation before operational use.

Monitoring: schema, missingness, distribution drift, prediction drift, calibration when labels arrive and subgroup performance.

Synthetic-data statement: all committed data and outputs are synthetic portfolio artefacts.
