# Portfolio integration and release-readiness

Milestone 18 consolidates the local Healthcare Enterprise Data Platform into one
reviewable portfolio experience.

The portfolio layer owns:

- final capability, technology and ownership matrices;
- golden-path local demonstration;
- consolidated evidence index;
- claim validation;
- architecture consistency review;
- v1.0 local release manifest;
- release-readiness report.

It does not deploy infrastructure, create a GitHub release, connect to cloud
services, generate screenshots, fabricate tenant evidence, claim compliance or
claim production readiness.

Run:

```bash
healthcare-platform demo validate
healthcare-platform demo run-golden-path
healthcare-platform demo generate-evidence --output-dir portfolio/reference --overwrite
healthcare-platform demo verify-evidence --output-dir portfolio/reference
```
