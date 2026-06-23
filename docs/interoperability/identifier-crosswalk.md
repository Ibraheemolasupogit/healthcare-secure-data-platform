# Identifier crosswalk

Version 1.0.0 maps FHIR resource IDs and HL7 patient, encounter, appointment, provider, organisation and pathology identifiers to the existing canonical IDs. The committed sample intentionally uses identity mappings because all inputs are synthetic views of Milestone 2 records.

Mappings are sorted and deterministic, use SHA-256 for operational IDs, reject conflicting source-to-canonical assignments and never use Python hashes. Unknown identifiers remain unmapped; no silent remapping occurs. A future reversible mapping would require explicit governance and protected storage.
