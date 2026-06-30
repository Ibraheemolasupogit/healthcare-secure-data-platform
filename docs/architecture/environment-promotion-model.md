# Environment promotion model

Promotion order is fixed: DEV, then TEST, then PROD. Each environment has a distinct
Terraform root, deployment identity placeholder and approval requirement in
`deployment/registry/deployment_controls.yaml`.

DEV permits platform-engineering review. TEST adds data-governance review. PROD requires
platform, security and governance review, separate reviewer representation, protected
release tags and no automatic apply.

