# Terraform plan review

Terraform validation uses `fmt`, `init -backend=false` and `validate`. Real plan artefacts
require protected credentials and approval. Any future plan must record commit SHA,
environment, Terraform/provider versions, variable-set identifier, checksum, creation time,
expiry and approval status.

Destructive changes, replacements, wildcard grants, public access, environment mismatch,
missing tags and sensitive outputs require fail-closed handling or elevated approval.

