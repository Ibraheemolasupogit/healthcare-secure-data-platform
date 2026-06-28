# Access-policy model

Access policies are centralised in `governance/registry/access_policies.yaml`.

Each policy defines subject, domain, object, environment, purpose, operation, effect,
conditions, classification, approval, masking, row policy, object policy, export policy,
audit requirement, owner, version, status and implementation mapping.

Unmatched requests return the explicit default-deny policy.
