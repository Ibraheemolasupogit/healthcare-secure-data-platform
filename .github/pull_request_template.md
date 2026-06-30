## Scope

Describe the milestone deliverable and why it belongs here.

## Explicit exclusions

State what this change deliberately does not implement.

## Validation and evidence

- [ ] `make validate`
- [ ] Relevant integration/platform checks
- [ ] Evidence is synthetic, redacted and traceable
- [ ] Deployment/release manifests updated when promotion controls change
- [ ] No live apply, deployment or rollback is claimed without evidence

## Security and data

- [ ] No real healthcare data, identifiers, credentials or account details
- [ ] Access/control changes include allowed and denied tests
- [ ] CI/CD changes keep pull-request validation credential-free

## Rollback

Describe safe reversal and any state/data implications.
