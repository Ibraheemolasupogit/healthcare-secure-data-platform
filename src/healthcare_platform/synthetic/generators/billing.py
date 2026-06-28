"""Deterministic synthetic healthcare billing and finance source generation."""

from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from healthcare_platform.synthetic import code_sets
from healthcare_platform.synthetic.generators.types import DatasetMap, Record
from healthcare_platform.synthetic.identifiers import stable_id
from healthcare_platform.synthetic.profiles import GenerationProfile

CENT = Decimal("0.01")
SOURCE_SYSTEM = "SYN-BILLING"


def money(value: Decimal | int | str) -> str:
    """Return source financial values as deterministic decimal strings."""
    return str(Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP))


def dt(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def d(value: date) -> str:
    return value.isoformat()


def _at(day: date, hour: int = 9) -> datetime:
    return datetime(day.year, day.month, day.day, hour, 0)


def generate_billing(
    profile: GenerationProfile,
    seed: int,
    reference_date: date,
    data: DatasetMap,
    inject_defects: bool = False,
    negative_test_mode: bool = False,
) -> DatasetMap:
    """Generate billing source domains linked to existing healthcare records."""
    _ = seed  # Billing uses deterministic source ordering; seed remains part of global provenance.
    billing: DatasetMap = {}
    updated_at = dt(_at(reference_date, 9))
    start_date = reference_date - timedelta(days=profile.historical_days)

    organisations = data["organisations"]
    encounters = data["encounters"]
    appointments = data["appointments"]
    clinical_events = data["clinical_events"]
    patients = {row["patient_id"]: row for row in data["patients"]}

    payers: list[Record] = []
    payer_types = code_sets.PAYER_TYPES
    for idx in range(1, profile.payer_count + 1):
        payer_type = payer_types[(idx - 1) % len(payer_types)]
        payers.append(
            {
                "payer_id": stable_id("payers", idx),
                "payer_code": f"SYN-PAYR-{idx:03d}",
                "payer_name": f"Synthetic {payer_type.replace('_', ' ').title()} {idx:03d}",
                "payer_type": payer_type,
                "organisation_id": organisations[(idx - 1) % len(organisations)]["organisation_id"]
                if payer_type in {"COMMISSIONER", "RESEARCH_SPONSOR"}
                else None,
                "active_flag": idx % 7 != 0,
                "valid_from": d(start_date),
                "valid_to": d(reference_date - timedelta(days=30)) if idx % 11 == 0 else None,
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
    billing["payers"] = payers

    services: list[Record] = []
    for idx in range(1, profile.service_count + 1):
        category = code_sets.SERVICE_CATEGORIES[(idx - 1) % len(code_sets.SERVICE_CATEGORIES)]
        specialty = code_sets.SPECIALTIES[(idx - 1) % len(code_sets.SPECIALTIES)]
        services.append(
            {
                "service_id": stable_id("services", idx),
                "service_code": f"SYN-SRV-{idx:03d}",
                "service_name": f"Synthetic {category.replace('_', ' ').title()}",
                "service_category": category,
                "specialty": specialty,
                "billable_flag": category != "ADMINISTRATIVE",
                "active_flag": True,
                "valid_from": d(start_date),
                "valid_to": None,
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
    billing["services"] = services

    products: list[Record] = []
    for idx in range(1, profile.product_count + 1):
        category = code_sets.PRODUCT_CATEGORIES[(idx - 1) % len(code_sets.PRODUCT_CATEGORIES)]
        products.append(
            {
                "product_id": stable_id("products", idx),
                "product_code": f"SYN-PRD-{idx:03d}",
                "product_name": f"Synthetic {category.replace('_', ' ').title()} {idx:03d}",
                "product_category": category,
                "unit_of_measure": "EACH",
                "billable_flag": True,
                "active_flag": True,
                "valid_from": d(start_date),
                "valid_to": None,
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
    billing["products"] = products

    tariffs: list[Record] = []
    for idx in range(1, profile.tariff_count + 1):
        service = services[(idx - 1) % len(services)]
        product = products[(idx - 1) % len(products)] if idx % 4 == 0 else None
        unit_price = Decimal("75.00") + Decimal(idx % 17) * Decimal("12.50")
        tariffs.append(
            {
                "tariff_id": stable_id("tariffs", idx),
                "tariff_code": f"SYN-TRF-{idx:03d}",
                "service_id": service["service_id"],
                "product_id": product["product_id"] if product else None,
                "payer_type": payer_types[(idx - 1) % len(payer_types)],
                "specialty": service["specialty"],
                "currency": "GBP",
                "unit_price": money(unit_price),
                "valid_from": d(start_date),
                "valid_to": None,
                "active_flag": True,
                "version": 1,
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
    if inject_defects or negative_test_mode:
        tariffs[0]["valid_to"] = d(start_date - timedelta(days=1))
    billing["tariffs"] = tariffs

    contracts: list[Record] = []
    for idx in range(1, profile.contract_count + 1):
        payer = payers[(idx - 1) % len(payers)]
        org = organisations[(idx - 1) % len(organisations)]
        contracts.append(
            {
                "contract_id": stable_id("contracts", idx),
                "contract_code": f"SYN-CTR-{idx:03d}",
                "payer_id": payer["payer_id"],
                "provider_organisation_id": org["organisation_id"],
                "contract_type": code_sets.CONTRACT_TYPES[
                    (idx - 1) % len(code_sets.CONTRACT_TYPES)
                ],
                "valid_from": d(start_date),
                "valid_to": d(reference_date - timedelta(days=60)) if idx % 9 == 0 else None,
                "currency": "GBP",
                "payment_terms_days": 30 + (idx % 3) * 15,
                "pricing_basis": code_sets.PRICING_BASES[(idx - 1) % len(code_sets.PRICING_BASES)],
                "status": "EXPIRED" if idx % 9 == 0 else "ACTIVE",
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
    billing["contracts"] = contracts

    latest_billable_activity_date = reference_date - timedelta(days=5)
    activity_candidates: list[Record] = []
    activity_candidates.extend(
        encounter
        for encounter in encounters
        if date.fromisoformat(encounter["start_datetime"][:10]) <= latest_billable_activity_date
    )
    activity_candidates.extend(
        appointment
        for appointment in appointments
        if date.fromisoformat(appointment["appointment_datetime"][:10])
        <= latest_billable_activity_date
    )
    activity_count = min(
        round(len(activity_candidates) * profile.billable_activity_rate), len(activity_candidates)
    )
    billable_activity: list[Record] = []
    for idx, source in enumerate(activity_candidates[:activity_count], start=1):
        is_appointment = "appointment_id" in source
        service = services[(idx - 1) % len(services)]
        product = products[(idx - 1) % len(products)] if idx % 5 == 0 else None
        patient = patients[source["patient_id"]]
        activity_time = (
            source["appointment_datetime"] if is_appointment else source["start_datetime"]
        )
        if negative_test_mode and idx == activity_count:
            activity_time = patient["birth_date"] + "T00:00:00Z"
        billable_activity.append(
            {
                "billable_activity_id": stable_id("billable_activity", idx),
                "patient_id": source["patient_id"],
                "encounter_id": None if is_appointment else source["encounter_id"],
                "appointment_id": source["appointment_id"] if is_appointment else None,
                "clinical_event_id": clinical_events[(idx - 1) % len(clinical_events)][
                    "clinical_event_id"
                ]
                if idx % 6 == 0
                else None,
                "service_id": service["service_id"],
                "product_id": product["product_id"] if product else None,
                "provider_id": source["provider_id"],
                "organisation_id": source["organisation_id"],
                "activity_datetime": activity_time,
                "quantity": money(Decimal("1") + Decimal(idx % 3)),
                "unit_of_measure": "EACH",
                "billing_status": "IDENTIFIED",
                "source_system": SOURCE_SYSTEM,
                "source_record_id": source["appointment_id"]
                if is_appointment
                else source["encounter_id"],
                "updated_at": updated_at,
            }
        )
    billing["billable_activity"] = billable_activity

    claim_count = round(len(billable_activity) * profile.claim_generation_rate)
    claims: list[Record] = []
    claim_lines: list[Record] = []
    for idx, activity in enumerate(billable_activity[:claim_count], start=1):
        payer = payers[(idx - 1) % len(payers)]
        contract = contracts[(idx - 1) % len(contracts)]
        tariff = tariffs[(idx - 1) % len(tariffs)]
        quantity = Decimal(str(activity["quantity"]))
        unit_price = Decimal(str(tariff["unit_price"]))
        line_amount = quantity * unit_price
        rejected = idx / max(claim_count, 1) <= profile.claim_rejection_rate
        claim_date = _at(
            datetime.fromisoformat(activity["activity_datetime"].replace("Z", "+00:00")).date()
            + timedelta(days=2)
        )
        claims.append(
            {
                "claim_id": stable_id("claims", idx),
                "claim_number": f"SYN-CLM-{idx:09d}",
                "patient_id": activity["patient_id"],
                "encounter_id": activity["encounter_id"],
                "payer_id": None
                if negative_test_mode and idx == claim_count
                else payer["payer_id"],
                "contract_id": contract["contract_id"],
                "claim_date": d(claim_date.date()),
                "service_period_start": activity["activity_datetime"][:10],
                "service_period_end": activity["activity_datetime"][:10],
                "claim_status": "REJECTED" if rejected else "ACCEPTED",
                "currency": "GBP",
                "claimed_amount": money(line_amount),
                "submitted_at": dt(claim_date),
                "adjudicated_at": dt(claim_date + timedelta(days=3)),
                "rejection_code": "SYN-REJECT" if rejected else None,
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
        claim_lines.append(
            {
                "claim_line_id": stable_id("claim_lines", idx),
                "claim_id": stable_id("claims", idx),
                "billable_activity_id": activity["billable_activity_id"],
                "service_id": activity["service_id"],
                "product_id": activity["product_id"],
                "tariff_id": tariff["tariff_id"],
                "quantity": money(quantity),
                "unit_price": money(unit_price),
                "line_amount": money(line_amount),
                "line_status": "REJECTED" if rejected else "ACCEPTED",
                "rejection_code": "SYN-REJECT" if rejected else None,
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
    billing["claims"] = claims
    billing["claim_lines"] = claim_lines

    invoice_count = round(len(billable_activity) * profile.invoice_generation_rate)
    invoices: list[Record] = []
    invoice_lines: list[Record] = []
    for idx, activity in enumerate(billable_activity[:invoice_count], start=1):
        payer = payers[(idx - 1) % len(payers)]
        contract = contracts[(idx - 1) % len(contracts)]
        tariff = tariffs[(idx - 1) % len(tariffs)]
        quantity = Decimal(str(activity["quantity"]))
        unit_price = Decimal(str(tariff["unit_price"]))
        net_amount = quantity * unit_price
        tax_amount = Decimal("0.00")
        gross_amount = net_amount + tax_amount
        invoice_date = datetime.fromisoformat(
            activity["activity_datetime"].replace("Z", "+00:00")
        ).date() + timedelta(days=5)
        invoices.append(
            {
                "invoice_id": stable_id("invoices", idx),
                "invoice_number": f"SYN-INV-{idx:09d}",
                "payer_id": payer["payer_id"],
                "patient_id": activity["patient_id"],
                "encounter_id": activity["encounter_id"],
                "contract_id": contract["contract_id"],
                "invoice_date": d(invoice_date),
                "due_date": d(invoice_date + timedelta(days=contract["payment_terms_days"])),
                "invoice_status": "ISSUED",
                "currency": "GBP",
                "subtotal_amount": money(net_amount),
                "tax_amount": money(tax_amount),
                "total_amount": money(gross_amount),
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
        invoice_lines.append(
            {
                "invoice_line_id": stable_id("invoice_lines", idx),
                "invoice_id": stable_id("invoices", idx),
                "billable_activity_id": activity["billable_activity_id"],
                "claim_line_id": stable_id("claim_lines", idx) if idx <= len(claim_lines) else None,
                "service_id": activity["service_id"],
                "product_id": activity["product_id"],
                "tariff_id": tariff["tariff_id"],
                "description": f"Synthetic billing line {idx:09d}",
                "quantity": money(quantity),
                "unit_price": money(unit_price),
                "net_amount": money(net_amount),
                "tax_amount": money(tax_amount),
                "gross_amount": money(gross_amount),
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
    if negative_test_mode and invoice_lines:
        invoice_lines[-1]["gross_amount"] = money(
            Decimal(str(invoice_lines[-1]["gross_amount"])) + Decimal("10.00")
        )
    billing["invoices"] = invoices
    billing["invoice_lines"] = invoice_lines

    attempt_count = round(len(invoices) * profile.payment_attempt_rate)
    attempts: list[Record] = []
    payments: list[Record] = []
    for idx, invoice in enumerate(invoices[:attempt_count], start=1):
        success = idx / max(attempt_count, 1) <= profile.payment_success_rate
        attempt_time = _at(date.fromisoformat(invoice["invoice_date"]) + timedelta(days=10), 10)
        attempts.append(
            {
                "payment_attempt_id": stable_id("payment_attempts", idx),
                "invoice_id": invoice["invoice_id"],
                "payer_id": invoice["payer_id"],
                "attempt_datetime": dt(attempt_time),
                "payment_method": code_sets.PAYMENT_METHODS[
                    (idx - 1) % len(code_sets.PAYMENT_METHODS)
                ],
                "requested_amount": invoice["total_amount"],
                "attempt_status": "SUCCESS" if success else "FAILED",
                "failure_code": None if success else "SYN_DECLINED",
                "gateway_reference": f"SYN-GW-{idx:012d}",
                "idempotency_key": f"SYN-IDEMP-{idx:012d}",
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
        if success:
            payments.append(
                {
                    "payment_id": stable_id("payments", len(payments) + 1),
                    "payment_attempt_id": stable_id("payment_attempts", idx),
                    "invoice_id": invoice["invoice_id"],
                    "payer_id": invoice["payer_id"],
                    "payment_datetime": dt(attempt_time + timedelta(hours=1)),
                    "amount": invoice["total_amount"],
                    "currency": invoice["currency"],
                    "payment_method": attempts[-1]["payment_method"],
                    "payment_status": "POSTED",
                    "external_reference": f"SYN-PAYREF-{idx:012d}",
                    "source_system": SOURCE_SYSTEM,
                    "updated_at": updated_at,
                }
            )
    if negative_test_mode and attempts:
        attempts[-1]["failure_code"] = None
    billing["payment_attempts"] = attempts
    billing["payments"] = payments

    refunds: list[Record] = []
    for idx, payment in enumerate(payments[: round(len(payments) * profile.refund_rate)], start=1):
        refunds.append(
            {
                "refund_id": stable_id("refunds", idx),
                "payment_id": payment["payment_id"],
                "invoice_id": payment["invoice_id"],
                "refund_datetime": dt(
                    datetime.fromisoformat(payment["payment_datetime"].replace("Z", "+00:00"))
                    + timedelta(days=2)
                ),
                "refund_amount": money(Decimal(str(payment["amount"])) * Decimal("0.25")),
                "refund_reason": "SYNTHETIC_GOODWILL",
                "refund_status": "PAID",
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
    if negative_test_mode and refunds:
        refunds[-1]["refund_amount"] = money(Decimal(str(payments[0]["amount"])) + Decimal("10.00"))
    billing["refunds"] = refunds

    adjustments: list[Record] = []
    for idx, invoice in enumerate(
        invoices[: round(len(invoices) * profile.adjustment_rate)], start=1
    ):
        adjustments.append(
            {
                "adjustment_id": stable_id("adjustments", idx),
                "invoice_id": invoice["invoice_id"],
                "claim_id": stable_id("claims", idx) if idx <= len(claims) else None,
                "adjustment_type": code_sets.ADJUSTMENT_TYPES[
                    (idx - 1) % len(code_sets.ADJUSTMENT_TYPES)
                ],
                "adjustment_reason": "SYNTHETIC_SOURCE_CORRECTION",
                "adjustment_datetime": dt(
                    _at(date.fromisoformat(invoice["invoice_date"]) + timedelta(days=12), 11)
                ),
                "adjustment_amount": money(Decimal("5.00")),
                "currency": invoice["currency"],
                "status": "POSTED",
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
    billing["adjustments"] = adjustments

    revenue_events: list[Record] = []
    ordinal = 1
    for line in invoice_lines:
        invoice = invoices[int(line["invoice_id"].split("-")[-1]) - 1]
        revenue_events.append(
            {
                "revenue_event_id": stable_id("revenue_events", ordinal),
                "invoice_id": line["invoice_id"],
                "invoice_line_id": line["invoice_line_id"],
                "claim_id": None,
                "billable_activity_id": line["billable_activity_id"],
                "event_type": "BILLED",
                "event_datetime": dt(_at(date.fromisoformat(invoice["invoice_date"]), 12)),
                "amount": line["gross_amount"],
                "currency": invoice["currency"],
                "source_status": invoice["invoice_status"],
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
        ordinal += 1
    for payment in payments:
        revenue_events.append(
            {
                "revenue_event_id": stable_id("revenue_events", ordinal),
                "invoice_id": payment["invoice_id"],
                "invoice_line_id": None,
                "claim_id": None,
                "billable_activity_id": None,
                "event_type": "COLLECTED",
                "event_datetime": payment["payment_datetime"],
                "amount": payment["amount"],
                "currency": payment["currency"],
                "source_status": payment["payment_status"],
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
        ordinal += 1
    billing["revenue_events"] = revenue_events

    payments_by_invoice = _sum_by(payments, "invoice_id", "amount")
    refunds_by_invoice = _sum_by(refunds, "invoice_id", "refund_amount")
    adjustments_by_invoice = _sum_by(adjustments, "invoice_id", "adjustment_amount")
    balances: list[Record] = []
    for idx, invoice in enumerate(invoices, start=1):
        total = Decimal(str(invoice["total_amount"]))
        paid = payments_by_invoice.get(invoice["invoice_id"], Decimal("0.00"))
        refunded = refunds_by_invoice.get(invoice["invoice_id"], Decimal("0.00"))
        adjusted = adjustments_by_invoice.get(invoice["invoice_id"], Decimal("0.00"))
        outstanding = total - paid + refunded - adjusted
        days_old = (reference_date - date.fromisoformat(invoice["invoice_date"])).days
        balances.append(
            {
                "balance_snapshot_id": stable_id("outstanding_balances", idx),
                "invoice_id": invoice["invoice_id"],
                "snapshot_date": d(reference_date),
                "invoiced_amount": money(total),
                "payment_amount": money(paid),
                "refund_amount": money(refunded),
                "adjustment_amount": money(adjusted),
                "outstanding_amount": money(outstanding),
                "ageing_bucket": _ageing_bucket(days_old),
                "currency": invoice["currency"],
                "source_system": SOURCE_SYSTEM,
                "updated_at": updated_at,
            }
        )
    if negative_test_mode and balances:
        balances[-1]["outstanding_amount"] = money(
            Decimal(str(balances[-1]["outstanding_amount"])) + Decimal("1.00")
        )
    billing["outstanding_balances"] = balances

    exceptions: list[Record] = []
    for idx, claim in enumerate(
        (row for row in claims if row["claim_status"] == "REJECTED"), start=1
    ):
        exceptions.append(_exception(idx, "REJECTED_CLAIM", claim, reference_date))
    if negative_test_mode:
        base = len(exceptions)
        exceptions.append(
            _exception(base + 1, "HEADER_LINE_MISMATCH", invoices[-1], reference_date)
        )
        exceptions.append(
            _exception(base + 2, "CONTROL_TOTAL_MISMATCH", invoices[-1], reference_date)
        )
    billing["billing_exceptions"] = exceptions

    billing["daily_control_totals"] = _control_totals(reference_date, billing)
    return billing


def _sum_by(rows: list[Record], key: str, amount: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in rows:
        totals[row[key]] = totals.get(row[key], Decimal("0.00")) + Decimal(str(row[amount]))
    return totals


def _ageing_bucket(days_old: int) -> str:
    if days_old <= 0:
        return "CURRENT"
    if days_old <= 30:
        return "DAYS_1_30"
    if days_old <= 60:
        return "DAYS_31_60"
    if days_old <= 90:
        return "DAYS_61_90"
    return "DAYS_90_PLUS"


def _exception(idx: int, exception_type: str, source: Record, reference_date: date) -> Record:
    return {
        "exception_id": stable_id("billing_exceptions", idx),
        "exception_type": exception_type
        if exception_type in code_sets.BILLING_EXCEPTION_TYPES
        else "INVALID_ADJUSTMENT",
        "source_system": SOURCE_SYSTEM,
        "source_record_id": str(
            source.get("claim_id") or source.get("invoice_id") or source.get("source_record_id")
        ),
        "patient_id": source.get("patient_id"),
        "encounter_id": source.get("encounter_id"),
        "billable_activity_id": source.get("billable_activity_id"),
        "claim_id": source.get("claim_id"),
        "invoice_id": source.get("invoice_id"),
        "payment_id": source.get("payment_id"),
        "severity": "WARNING",
        "financial_value_at_risk": money(
            source.get("claimed_amount") or source.get("total_amount") or "0.00"
        ),
        "detected_at": dt(_at(reference_date, 12)),
        "assigned_owner": "SYNTHETIC_BILLING_CONTROL",
        "status": "OPEN",
        "resolution_date": None,
        "root_cause": "SYNTHETIC_PORTFOLIO_RULE",
        "remediation_action": "REVIEW_IN_MILESTONE_9",
        "synthetic_flag": True,
    }


def _control_totals(reference_date: date, billing: DatasetMap) -> list[Record]:
    specs = (
        ("INVOICES", billing["invoices"], "total_amount"),
        ("INVOICE_LINES", billing["invoice_lines"], "gross_amount"),
        ("PAYMENTS", billing["payments"], "amount"),
        ("REFUNDS", billing["refunds"], "refund_amount"),
        ("ADJUSTMENTS", billing["adjustments"], "adjustment_amount"),
    )
    controls: list[Record] = []
    for idx, (entity_type, rows, amount_field) in enumerate(specs, start=1):
        gross = sum((Decimal(str(row.get(amount_field, "0.00"))) for row in rows), Decimal("0.00"))
        controls.append(
            {
                "control_total_id": stable_id("daily_control_totals", idx),
                "control_date": d(reference_date),
                "source_system": SOURCE_SYSTEM,
                "entity_type": entity_type,
                "record_count": len(rows),
                "gross_amount": money(gross),
                "net_amount": money(gross),
                "payment_amount": money(gross if entity_type == "PAYMENTS" else Decimal("0.00")),
                "refund_amount": money(gross if entity_type == "REFUNDS" else Decimal("0.00")),
                "adjustment_amount": money(
                    gross if entity_type == "ADJUSTMENTS" else Decimal("0.00")
                ),
                "currency": "GBP",
                "generated_at": dt(_at(reference_date, 13)),
                "checksum": f"SYN-CONTROL-{entity_type}-{len(rows)}-{money(gross)}",
            }
        )
    return controls
