# Canonical ingestion envelope

FHIR and HL7 payloads share one immutable audit envelope. It records source format/system/type/IDs, canonical patient and encounter IDs, event and receipt times, parser/schema versions, validation outcome, counts, checksum, correlation/batch IDs, quarantine state, raw path, environment and synthetic marker.

The envelope is source-neutral operational metadata. It does not replace patient, encounter or other Milestone 2 domain schemas. Its static Snowflake destination is `RAW.AUDIT`; original payloads remain in `RAW.INTEROPERABILITY` and rejected payload metadata in `RAW.QUARANTINE`.
