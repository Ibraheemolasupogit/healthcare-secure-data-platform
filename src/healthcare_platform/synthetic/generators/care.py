"""Deterministic synthetic care activity generators."""

from collections import defaultdict
from datetime import date, datetime, timedelta

from healthcare_platform.synthetic import code_sets
from healthcare_platform.synthetic.generators.common import (
    at_utc,
    iso_date,
    iso_datetime,
    random_date,
)
from healthcare_platform.synthetic.generators.types import DatasetMap, Record
from healthcare_platform.synthetic.identifiers import stable_id
from healthcare_platform.synthetic.profiles import GenerationProfile
from healthcare_platform.synthetic.random_streams import stream


def generate_care(
    profile: GenerationProfile, seed: int, reference_date: date, base: DatasetMap
) -> DatasetMap:
    encounters = _encounters(profile, seed, reference_date, base)
    admissions = _admissions(profile, seed, encounters)
    appointments = _appointments(profile, seed, reference_date, base)
    clinical_events = _clinical_events(profile, seed, encounters, appointments)
    return {
        "encounters": encounters,
        "admissions": admissions,
        "appointments": appointments,
        "pathways": _pathways(profile, seed, reference_date, base),
        "clinical_events": clinical_events,
        "pathology_results": _pathology(profile, seed, base, encounters),
        "medication_events": _medications(profile, seed, encounters),
    }


def _activity_bounds(
    patient: Record, profile: GenerationProfile, reference_date: date
) -> tuple[date, date]:
    birth = date.fromisoformat(patient["birth_date"])
    start = max(
        birth + timedelta(days=18 * 365), reference_date - timedelta(days=profile.historical_days)
    )
    end = date.fromisoformat(patient["death_date"]) if patient["death_date"] else reference_date
    return start, max(start, end)


def _by_org(records: list[Record]) -> dict[str, list[Record]]:
    grouped: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        grouped[record["organisation_id"]].append(record)
    return grouped


def _encounters(
    profile: GenerationProfile, seed: int, reference_date: date, base: DatasetMap
) -> list[Record]:
    rng = stream(seed, "encounters")
    locations = _by_org(base["locations"])
    providers = _by_org(base["providers"])
    organisation_ids = list(locations)
    count = profile.estimated_rows()["encounters"]
    rows: list[Record] = []
    for ordinal in range(1, count + 1):
        patient = base["patients"][(ordinal - 1) % len(base["patients"])]
        start_bound, end_bound = _activity_bounds(patient, profile, reference_date)
        day = random_date(rng, start_bound, end_bound)
        start = at_utc(day, rng.randint(0, 20), rng.choice((0, 15, 30, 45)))
        organisation_id = rng.choice(organisation_ids)
        encounter_type = rng.choices(code_sets.ENCOUNTER_TYPES, weights=(15, 25, 30, 15, 15), k=1)[
            0
        ]
        duration_hours = (
            rng.randint(1, 12) if encounter_type != "INPATIENT" else rng.randint(24, 240)
        )
        end = start + timedelta(hours=duration_hours)
        if end.date() > end_bound:
            end = at_utc(end_bound, 23, 59)
        rows.append(
            {
                "encounter_id": stable_id("encounters", ordinal),
                "patient_id": patient["patient_id"],
                "organisation_id": organisation_id,
                "location_id": rng.choice(locations[organisation_id])["location_id"],
                "provider_id": rng.choice(providers[organisation_id])["provider_id"],
                "encounter_type": encounter_type,
                "admission_method": rng.choice(("ELECTIVE", "EMERGENCY", "TRANSFER"))
                if encounter_type == "INPATIENT"
                else None,
                "start_datetime": iso_datetime(start),
                "end_datetime": iso_datetime(end),
                "status": "COMPLETED",
                "discharge_destination": rng.choice(("HOME", "TRANSFER", "COMMUNITY"))
                if encounter_type == "INPATIENT"
                else None,
                "primary_diagnosis_code": f"SYN-DX-{rng.randint(1, 20):02d}",
                "source_system": rng.choice(("SYN-EPR", "SYN-PAS", "SYN-COMMUNITY")),
                "updated_at": iso_datetime(end + timedelta(minutes=5)),
            }
        )
    return rows


def _admissions(profile: GenerationProfile, seed: int, encounters: list[Record]) -> list[Record]:
    rng = stream(seed, "admissions")
    desired = profile.estimated_rows()["admissions"]
    eligible = [row for row in encounters if row["encounter_type"] == "INPATIENT"][:desired]
    eligible.sort(key=lambda row: (row["patient_id"], row["start_datetime"]))
    previous: dict[str, str] = {}
    rows: list[Record] = []
    for ordinal, encounter in enumerate(eligible, 1):
        admission = datetime.fromisoformat(encounter["start_datetime"].replace("Z", "+00:00"))
        discharge = datetime.fromisoformat(encounter["end_datetime"].replace("Z", "+00:00"))
        open_admission = ordinal % 10 == 0
        prior = previous.get(encounter["patient_id"])
        admission_id = stable_id("admissions", ordinal)
        rows.append(
            {
                "admission_id": admission_id,
                "encounter_id": encounter["encounter_id"],
                "patient_id": encounter["patient_id"],
                "admission_datetime": encounter["start_datetime"],
                "discharge_datetime": None if open_admission else encounter["end_datetime"],
                "admission_method": encounter["admission_method"],
                "discharge_method": None
                if open_admission
                else rng.choice(("CLINICAL_DISCHARGE", "TRANSFER", "SELF_DISCHARGE")),
                "ward_id": encounter["location_id"],
                "length_of_stay_days": None
                if open_admission
                else (discharge.date() - admission.date()).days,
                "readmission_flag": prior is not None,
                "prior_admission_id": prior,
                "updated_at": encounter["updated_at"],
            }
        )
        previous[encounter["patient_id"]] = admission_id
        if open_admission:
            encounter["end_datetime"] = None
            encounter["status"] = "IN_PROGRESS"
            encounter["discharge_destination"] = None
    return rows


def _appointments(
    profile: GenerationProfile, seed: int, reference_date: date, base: DatasetMap
) -> list[Record]:
    rng = stream(seed, "appointments")
    locations = _by_org(base["locations"])
    providers = _by_org(base["providers"])
    organisation_ids = list(locations)
    living = [patient for patient in base["patients"] if not patient["deceased_flag"]]
    count = profile.estimated_rows()["appointments"]
    rows: list[Record] = []
    for ordinal in range(1, count + 1):
        patient = living[(ordinal - 1) % len(living)]
        start_bound, _ = _activity_bounds(patient, profile, reference_date)
        appointment_day = random_date(
            rng, start_bound, reference_date + timedelta(days=profile.future_horizon_days)
        )
        appointment = at_utc(appointment_day, rng.randint(8, 17), rng.choice((0, 15, 30, 45)))
        booking = appointment - timedelta(days=rng.randint(1, 120), hours=rng.randint(0, 8))
        organisation_id = rng.choice(organisation_ids)
        if appointment_day > reference_date:
            status = "BOOKED"
        else:
            status = rng.choice(("ATTENDED", "DID_NOT_ATTEND", "CANCELLED"))
        rows.append(
            {
                "appointment_id": stable_id("appointments", ordinal),
                "patient_id": patient["patient_id"],
                "organisation_id": organisation_id,
                "location_id": rng.choice(locations[organisation_id])["location_id"],
                "provider_id": rng.choice(providers[organisation_id])["provider_id"],
                "appointment_datetime": iso_datetime(appointment),
                "booking_datetime": iso_datetime(booking),
                "appointment_type": rng.choice(("NEW", "FOLLOW_UP", "DIAGNOSTIC")),
                "attendance_status": status,
                "cancellation_reason": rng.choice(("PATIENT_REQUEST", "PROVIDER_UNAVAILABLE"))
                if status == "CANCELLED"
                else None,
                "referral_id": stable_id("clinical_events", ordinal),
                "updated_at": iso_datetime(
                    min(appointment, at_utc(reference_date)) + timedelta(minutes=5)
                ),
            }
        )
    return rows


def _clinical_events(
    profile: GenerationProfile, seed: int, encounters: list[Record], appointments: list[Record]
) -> list[Record]:
    rng = stream(seed, "clinical_events")
    count = profile.estimated_rows()["clinical_events"]
    encounters_by_patient: dict[str, list[Record]] = defaultdict(list)
    for encounter in encounters:
        encounters_by_patient[encounter["patient_id"]].append(encounter)
    rows: list[Record] = []
    for ordinal in range(1, count + 1):
        if ordinal <= len(appointments):
            appointment = appointments[ordinal - 1]
            patient_id = appointment["patient_id"]
            event_type = "REFERRAL"
        else:
            encounter_seed = encounters[(ordinal - 1) % len(encounters)]
            patient_id = encounter_seed["patient_id"]
            event_type = rng.choice(code_sets.CLINICAL_EVENT_TYPES)
        encounter = rng.choice(encounters_by_patient[patient_id])
        start = datetime.fromisoformat(encounter["start_datetime"].replace("Z", "+00:00"))
        end = (
            datetime.fromisoformat(encounter["end_datetime"].replace("Z", "+00:00"))
            if encounter["end_datetime"]
            else start + timedelta(hours=1)
        )
        event_time = start + (end - start) / 2
        rows.append(
            {
                "clinical_event_id": stable_id("clinical_events", ordinal),
                "patient_id": patient_id,
                "encounter_id": encounter["encounter_id"],
                "provider_id": encounter["provider_id"],
                "event_type": event_type,
                "event_code": f"SYN-{event_type[:3]}-{rng.randint(1, 30):02d}",
                "event_value": str(rng.randint(50, 180))
                if event_type == "OBSERVATION"
                else "SYNTHETIC_CODED_VALUE",
                "event_unit": "synthetic-unit" if event_type == "OBSERVATION" else None,
                "event_datetime": iso_datetime(event_time),
                "source_system": encounter["source_system"],
                "updated_at": iso_datetime(event_time + timedelta(minutes=5)),
            }
        )
    return rows


def _pathways(
    profile: GenerationProfile, seed: int, reference_date: date, base: DatasetMap
) -> list[Record]:
    rng = stream(seed, "pathways")
    living = [patient for patient in base["patients"] if not patient["deceased_flag"]]
    organisation_ids = [row["organisation_id"] for row in base["organisations"]]
    statuses = ("ACTIVE", "COMPLETED", "CANCELLED", "TRANSFERRED")
    rows: list[Record] = []
    for ordinal in range(1, profile.estimated_rows()["pathways"] + 1):
        patient = living[(ordinal - 1) % len(living)]
        earliest, _ = _activity_bounds(patient, profile, reference_date)
        clock_start = random_date(rng, earliest, reference_date - timedelta(days=1))
        status = statuses[(ordinal - 1) % len(statuses)]
        completion = None
        if status != "ACTIVE":
            completion = random_date(rng, clock_start, reference_date)
        endpoint = completion or reference_date
        waiting_days = (endpoint - clock_start).days
        stage = {
            "ACTIVE": rng.choice(code_sets.PATHWAY_STAGES[:6]),
            "COMPLETED": "COMPLETED",
            "CANCELLED": "CANCELLED",
            "TRANSFERRED": "TRANSFERRED",
        }[status]
        rows.append(
            {
                "pathway_id": stable_id("pathways", ordinal),
                "patient_id": patient["patient_id"],
                "referral_date": iso_date(clock_start),
                "pathway_type": rng.choice(("RTT", "DIAGNOSTIC", "CANCER_LIKE_SYNTHETIC")),
                "specialty": rng.choice(code_sets.SPECIALTIES),
                "organisation_id": rng.choice(organisation_ids),
                "clock_start_date": iso_date(clock_start),
                "current_status": status,
                "current_stage": stage,
                "target_date": iso_date(clock_start + timedelta(days=126)),
                "completion_date": iso_date(completion) if completion else None,
                "waiting_days": waiting_days,
                "breach_flag": waiting_days > 126,
                "updated_at": iso_datetime(at_utc(endpoint)),
            }
        )
    return rows


def _pathology(
    profile: GenerationProfile, seed: int, base: DatasetMap, encounters: list[Record]
) -> list[Record]:
    rng = stream(seed, "pathology")
    laboratories = [
        row["organisation_id"]
        for row in base["organisations"]
        if row["organisation_type"] == "LABORATORY"
    ] or [base["organisations"][0]["organisation_id"]]
    tests = (
        ("SYN-HB", "Synthetic haemoglobin", "g/L", 120.0, 170.0),
        ("SYN-CRP", "Synthetic inflammatory marker", "mg/L", 0.0, 5.0),
        ("SYN-NA", "Synthetic sodium", "mmol/L", 135.0, 145.0),
    )
    rows: list[Record] = []
    for ordinal in range(1, profile.estimated_rows()["pathology_results"] + 1):
        encounter = encounters[(ordinal - 1) % len(encounters)]
        specimen = datetime.fromisoformat(encounter["start_datetime"].replace("Z", "+00:00"))
        code, name, unit, low, high = tests[(ordinal - 1) % len(tests)]
        value = round(rng.uniform(low - (high - low) * 0.3, high + (high - low) * 0.3), 2)
        result_time = specimen + timedelta(hours=rng.randint(1, 48))
        rows.append(
            {
                "pathology_result_id": stable_id("pathology_results", ordinal),
                "patient_id": encounter["patient_id"],
                "encounter_id": encounter["encounter_id"],
                "requesting_provider_id": encounter["provider_id"],
                "laboratory_organisation_id": rng.choice(laboratories),
                "test_code": code,
                "test_name": name,
                "result_value": value,
                "result_unit": unit,
                "reference_low": low,
                "reference_high": high,
                "abnormal_flag": value < low or value > high,
                "specimen_datetime": iso_datetime(specimen),
                "result_datetime": iso_datetime(result_time),
                "status": rng.choice(code_sets.PATHOLOGY_STATUSES),
                "updated_at": iso_datetime(result_time + timedelta(minutes=5)),
            }
        )
    return rows


def _medications(profile: GenerationProfile, seed: int, encounters: list[Record]) -> list[Record]:
    rng = stream(seed, "medications")
    rows: list[Record] = []
    for ordinal in range(1, profile.estimated_rows()["medication_events"] + 1):
        encounter = encounters[(ordinal - 1) % len(encounters)]
        event_time = datetime.fromisoformat(encounter["start_datetime"].replace("Z", "+00:00"))
        medication_number = (ordinal % 12) + 1
        event_type = rng.choice(code_sets.MEDICATION_EVENT_TYPES)
        rows.append(
            {
                "medication_event_id": stable_id("medication_events", ordinal),
                "patient_id": encounter["patient_id"],
                "encounter_id": encounter["encounter_id"],
                "provider_id": encounter["provider_id"],
                "medication_code": f"SYN-MED-{medication_number:02d}",
                "medication_name": f"Synthetic Medicine {medication_number:02d}",
                "event_type": event_type,
                "dose": float(rng.choice((1, 2, 5, 10, 20))),
                "dose_unit": "mg",
                "route": rng.choice(("ORAL", "INTRAVENOUS", "TOPICAL")),
                "event_datetime": iso_datetime(event_time),
                "status": "ACTIVE" if event_type == "PRESCRIPTION" else "COMPLETED",
                "updated_at": iso_datetime(event_time + timedelta(minutes=5)),
            }
        )
    return rows
