# Feature registry management

Update registry YAML files under `feature_store/registry`.

Rules:

- do not change definitions silently;
- increment version when behaviour changes;
- keep previous versions discoverable;
- declare exact consumers;
- document lifecycle status;
- validate with `healthcare-platform feature-store validate-registry`.
