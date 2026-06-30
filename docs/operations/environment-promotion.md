# Environment promotion

Promotion uses exact commit and exact artefact continuity from DEV to TEST to PROD. Failed
validation blocks promotion. Self-approval is prohibited. PROD requires separate reviewer
representation and must not run automatically from a push to `main`.

Milestone 15 provides local metadata and evidence only; it does not configure live GitHub
environments.

