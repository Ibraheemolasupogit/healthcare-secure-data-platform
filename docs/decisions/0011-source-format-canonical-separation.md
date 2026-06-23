# ADR 0011: Separate source formats from the canonical healthcare model

- **Status:** Accepted
- **Date:** 2026-06-23

## Context

FHIR and HL7 representations could accidentally become competing patient and encounter models or leak source parsing into future transformations.

## Decision

Milestone 2 schemas remain authoritative. FHIR-inspired resources and HL7 messages are source-format views. A source-neutral ingestion envelope owns audit metadata only; identifier crosswalks explicitly map to canonical IDs. Original payloads target RAW while future dbt work owns transformations.

## Consequences

Source fidelity and unmapped fields are retained without redefining business entities. Adding a format requires a parser/mapper, not new canonical domains. Formal standards conformance remains independently evidenced.

## Alternatives considered

A generic interoperability domain model was rejected because it would duplicate working schemas. Direct source-to-dbt parsing was rejected because it weakens immutable RAW, quarantine and replay boundaries.

## Validation

Tests assert canonical ID reuse, reference resolution, crosswalk conflict rejection, envelope scope and Snowflake contract placement.
