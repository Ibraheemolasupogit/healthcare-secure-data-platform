# Tariff and contract matching

Tariff selection is centralised in `int_billing__selected_tariff`.

The deterministic priority is:

1. Product match where a product exists.
2. Service match.
3. Effective date match.
4. Active tariff.
5. Highest version.
6. Lowest tariff identifier as final deterministic tie-break.

Contract selection is centralised in `int_billing__selected_contract`.

The deterministic priority is:

1. Source contract identifier.
2. Payer match.
3. Currency compatibility.
4. Effective date match.
5. Active contract.
6. Lowest contract identifier as final deterministic tie-break.

Both paths expose candidate counts, match status and selection reason. They do not silently discard unmatched or ambiguous records.

