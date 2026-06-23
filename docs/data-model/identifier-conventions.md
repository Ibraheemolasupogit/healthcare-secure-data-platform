# Identifier conventions

Identifiers use an uppercase three-letter prefix, hyphen and nine-digit one-based ordinal: `PAT-000000001`, `ENC-000000001`, `ADM-000000001`, `APT-000000001`, and `PTH-000000001`. Other prefixes are defined centrally in `identifiers.py`.

Identifiers are allocated by stable canonical generation order. They never use Python's process-randomised `hash()`, UUID randomness, real identifiers, or source-system values. Provider labels use `Provider-000001`. Patient external-style identifiers use `SYN-NHS-000000001`; the `SYN-` marker deliberately prevents confusion with a real NHS number and no modulus/check-digit claim is made.

Domain random streams are derived from `SHA-256(seed:domain)`. Patient pseudonyms are derived separately from seed and ordinal. Changing a domain algorithm may change values within that domain, so generator version and configuration hash are part of provenance.
