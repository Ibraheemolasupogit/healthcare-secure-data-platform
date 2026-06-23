# Schema versioning

All canonical datasets currently use schema version `1.0.0`. Schema metadata is source-controlled and exported to `schema_catalog.json` on every run.

Use semantic versioning:

- patch: descriptions or classifications clarified without changing representation;
- minor: backward-compatible nullable field or controlled code added;
- major: removed/renamed field, type/nullability change, key/grain change or semantic reinterpretation.

Generated artifacts record the version per dataset. A breaking change requires migration notes, updated validators and fixtures, a generator version bump, and later dbt source-contract coordination. This milestone does not create dbt models.
