# FHIR-inspired scope

Milestone 4 supports synthetic, simplified JSON views for Patient, Organization, Location, Practitioner, Encounter, Appointment, Observation, DiagnosticReport, MedicationRequest and Consent. These views reuse Milestone 2 identifiers and records; they are not a second healthcare domain model.

Every resource has `resourceType`, a stable synthetic `id`, version/source metadata, a synthetic provenance tag, identifiers where appropriate, statuses and resolvable references. Collection, transaction-style and batch-style bundles are examples only. No live transaction behaviour is implemented.

The parser dispatches supported types, extracts identifiers/references/status/time, preserves the raw resource and extensions, and records unmapped fields. Validation checks required fields, synthetic IDs, statuses, timestamps, periods, provenance and bundle references.

This is not full FHIR R4 conformance. Profiles, cardinalities, terminology bindings, narrative, server interactions and formal validator evidence are absent. A future path would pin named implementation guides and run a recognised validator against versioned profiles.
