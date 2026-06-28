from datetime import date
from decimal import Decimal

from healthcare_platform.synthetic.generators import generate_all
from healthcare_platform.synthetic.generators.types import DatasetMap
from healthcare_platform.synthetic.profiles import load_profile
from healthcare_platform.synthetic.validation import validate


def _data(negative: bool = False) -> DatasetMap:
    profile = load_profile("small").with_patient_count(12)
    return generate_all(profile, 42, date(2025, 1, 1), negative, negative)


def test_billing_generation_links_to_healthcare_sources_and_validates() -> None:
    data = _data()
    report = validate(data, date(2025, 1, 1))
    assert report.valid, report.issues
    assert data["payers"]
    assert data["billable_activity"]
    assert data["invoices"]
    assert data["payments"]
    healthcare_source_ids = {
        *(row["encounter_id"] for row in data["encounters"]),
        *(row["appointment_id"] for row in data["appointments"]),
    }
    assert {row["source_record_id"] for row in data["billable_activity"]}.issubset(
        healthcare_source_ids
    )


def test_billing_amounts_use_decimal_safe_source_identities() -> None:
    data = _data()
    invoice_lines_by_invoice: dict[str, list[dict[str, object]]] = {}
    for line in data["invoice_lines"]:
        assert Decimal(str(line["net_amount"])) == Decimal(str(line["quantity"])) * Decimal(
            str(line["unit_price"])
        )
        assert Decimal(str(line["gross_amount"])) == Decimal(str(line["net_amount"])) + Decimal(
            str(line["tax_amount"])
        )
        invoice_lines_by_invoice.setdefault(str(line["invoice_id"]), []).append(line)

    for invoice in data["invoices"]:
        lines = invoice_lines_by_invoice[str(invoice["invoice_id"])]
        assert Decimal(str(invoice["subtotal_amount"])) == sum(
            (Decimal(str(line["net_amount"])) for line in lines), Decimal("0.00")
        )
        assert Decimal(str(invoice["total_amount"])) == sum(
            (Decimal(str(line["gross_amount"])) for line in lines), Decimal("0.00")
        )


def test_billing_negative_mode_surfaces_financial_defects() -> None:
    data = _data(negative=True)
    report = validate(data, date(2025, 1, 1))
    assert not report.valid
    rule_ids = {issue.rule_id for issue in report.issues}
    assert {
        "FIN-INVL-002",
        "FIN-INV-002",
        "BR-PATM-001",
        "FIN-BAL-001",
    }.issubset(rule_ids)
