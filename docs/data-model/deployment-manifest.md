# Deployment manifest model

Per-environment deployment manifests record deployment ID, release ID, environment,
planned Terraform artefact name, plan checksum placeholder, apply status, actor type,
service identity, approval references, resource-change counts, platform artefact
references, evidence references, rollback reference and limitations.

For Milestone 15 every apply status is `NOT_EXECUTED`.

