# Release manifest model

`deployment/reference/release_manifest.json` records release ID, repository, commit SHA,
branch, milestone, version, target environments, artefacts, tool versions, governance
validation status, test status, deployment status, approval status, rollback reference,
limitations and a synthetic-only flag.

The manifest is deterministic local evidence. It is not a GitHub release and does not
represent a production deployment.

