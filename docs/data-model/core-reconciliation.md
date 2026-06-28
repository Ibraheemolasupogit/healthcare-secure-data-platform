# Core reconciliation

Milestone 6 surfaces reconciliation outcomes instead of hiding them.

Implemented outputs:

- `core_reconciliation_exceptions`
- `core_reconciliation_row_counts`

Covered exception classes:

- unmatched patient identifiers
- unmatched encounter identifiers
- conflicting patient or encounter mappings
- orphan patient, organisation, location or provider references
- source-to-core row-count differences

The exception outputs are governed audit models, not business marts.
