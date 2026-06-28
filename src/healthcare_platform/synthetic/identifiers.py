"""Stable identifier conventions independent of Python hash randomisation."""

PREFIXES = {
    "organisations": "ORG",
    "locations": "LOC",
    "providers": "PRV",
    "patients": "PAT",
    "encounters": "ENC",
    "admissions": "ADM",
    "appointments": "APT",
    "pathways": "PTH",
    "clinical_events": "CLE",
    "pathology_results": "LAB",
    "medication_events": "MED",
    "research_consent": "CON",
    "research_cohorts": "COH",
    "audit_events": "AUD",
    "data_quality_events": "DQE",
    "payers": "PAYR",
    "services": "SRV",
    "products": "PRD",
    "tariffs": "TRF",
    "contracts": "CTR",
    "billable_activity": "BACT",
    "claims": "CLM",
    "claim_lines": "CLML",
    "invoices": "INV",
    "invoice_lines": "INVL",
    "payment_attempts": "PATM",
    "payments": "PAY",
    "refunds": "REF",
    "adjustments": "ADJ",
    "billing_exceptions": "BEX",
    "revenue_events": "REV",
    "outstanding_balances": "BAL",
    "daily_control_totals": "CTL",
}


def stable_id(dataset: str, ordinal: int) -> str:
    """Return a stable, visibly synthetic identifier."""
    if dataset not in PREFIXES or ordinal < 1:
        raise ValueError("dataset must be known and ordinal must be positive")
    return f"{PREFIXES[dataset]}-{ordinal:09d}"
