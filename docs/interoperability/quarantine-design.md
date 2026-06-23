# Interoperability quarantine design

Validation classifies payloads as accepted, accepted with warnings, rejected or unsupported. Duplicate and conflicting identifiers have explicit error paths. Rejected payloads are retained with deterministic quarantine ID, validation/warning codes, checksum, safe relative raw path, parser/schema version, retry eligibility, disposition and synthetic marker.

Retry eligibility is rule-based: malformed JSON/timestamps and unresolved references may be correctable; unsupported formats require contract review. Nothing is discarded silently. The committed negative corpus is isolated from clean samples and produces eight quarantine records.
