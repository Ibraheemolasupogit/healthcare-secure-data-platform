# Learning-to-implementation log

Use one entry per applied concept. Paraphrase learning in your own words; never copy proprietary course text or code.

## Entry: YYYY-MM-DD — concise concept

- **Concept studied:**
- **Source or course section:** citation/reference only
- **Healthcare adaptation:** why the context changes the design
- **Implementation location:** files/objects
- **Validation performed:** command and expected/actual result
- **Architecture decision:** ADR link or “none required”
- **Evidence captured:** durable evidence path
- **Portfolio value:** capability demonstrated without exaggeration
- **Lessons learned:** trade-offs and next improvement

## Entry: 2026-06-28 — billing source generation before finance transformation

- **Concept studied:** separate source-system fixtures from governed transformation logic.
- **Source or course section:** project Milestone 7 implementation.
- **Healthcare adaptation:** billing events must remain traceable to care activity while avoiding real payer, card, bank or patient identifiers.
- **Implementation location:** `src/healthcare_platform/synthetic`, `config/synthetic/profiles.json`, `data/samples/small`, `data/negative_tests/billing`.
- **Validation performed:** focused billing/source pytest slice and generator validation.
- **Architecture decision:** [ADR 0013](../decisions/0013-billing-source-generation-boundary.md).
- **Evidence captured:** [Milestone 7 evidence](../evidence/milestone-7-evidence.md).
- **Portfolio value:** demonstrates deterministic finance-source controls without overstating revenue-recognition or mart readiness.
- **Lessons learned:** source arithmetic can be validated locally with `Decimal`; downstream allocation and accounting policy should remain in dbt milestones.
