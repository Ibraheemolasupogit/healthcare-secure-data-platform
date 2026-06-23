# HL7 v2 scope

Milestone 4 supports synthetic HL7 v2.5 messages for ADT^A01, ADT^A03, ADT^A08, ORM^O01, ORU^R01 and SIU^S12. The focused parser handles MSH, EVN, PID, PV1, ORC, OBR, OBX, SCH, AIP and NTE, preserving unknown segments with warnings.

Validation checks MSH ordering, separators, version, message type, control ID, timestamp, required segments, patient/encounter or appointment identifiers, and basic order/result value-unit consistency. IDs map directly to existing Milestone 2 records.

This is a bounded portfolio parser, not production HL7 integration. It does not implement MLLP, sockets, acknowledgements, profiles, full escaping, every repetition/cardinality rule, live interfaces or vendor-specific variants.
