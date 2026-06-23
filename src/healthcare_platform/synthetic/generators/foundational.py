"""Organisation, location, provider and patient generation."""

import hashlib
from datetime import date, timedelta

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


def generate_foundational(
    profile: GenerationProfile, seed: int, reference_date: date
) -> DatasetMap:
    organisations = _organisations(profile, reference_date)
    locations = _locations(profile, seed, organisations)
    providers = _providers(profile, seed, reference_date, organisations)
    patients = _patients(profile, seed, reference_date, organisations)
    return {
        "organisations": organisations,
        "locations": locations,
        "providers": providers,
        "patients": patients,
    }


def _organisations(profile: GenerationProfile, reference_date: date) -> list[Record]:
    records: list[Record] = []
    for ordinal in range(1, profile.organisation_count + 1):
        organisation_type = code_sets.ORGANISATION_TYPES[
            (ordinal - 1) % len(code_sets.ORGANISATION_TYPES)
        ]
        records.append(
            {
                "organisation_id": stable_id("organisations", ordinal),
                "organisation_code": f"SYN-ORG-{ordinal:03d}",
                "organisation_name": (
                    f"Synthetic {organisation_type.replace('_', ' ').title()} {ordinal:03d}"
                ),
                "organisation_type": organisation_type,
                "parent_organisation_id": stable_id("organisations", 1) if ordinal > 6 else None,
                "region": ("SYNTHETIC_NORTH", "SYNTHETIC_CENTRAL", "SYNTHETIC_SOUTH")[
                    (ordinal - 1) % 3
                ],
                "active_flag": True,
                "valid_from": iso_date(reference_date - timedelta(days=3650)),
                "valid_to": None,
            }
        )
    return records


def _locations(profile: GenerationProfile, seed: int, organisations: list[Record]) -> list[Record]:
    rng = stream(seed, "locations")
    records: list[Record] = []
    ordinal = 1
    for organisation in organisations:
        for _ in range(profile.locations_per_organisation):
            location_type = rng.choice(code_sets.LOCATION_TYPES)
            records.append(
                {
                    "location_id": stable_id("locations", ordinal),
                    "organisation_id": organisation["organisation_id"],
                    "location_code": f"SYN-LOC-{ordinal:04d}",
                    "location_name": (
                        f"Synthetic {location_type.replace('_', ' ').title()} {ordinal:04d}"
                    ),
                    "location_type": location_type,
                    "specialty": rng.choice(code_sets.SPECIALTIES),
                    "active_flag": True,
                }
            )
            ordinal += 1
    return records


def _providers(
    profile: GenerationProfile, seed: int, reference_date: date, organisations: list[Record]
) -> list[Record]:
    rng = stream(seed, "providers")
    records: list[Record] = []
    ordinal = 1
    for organisation in organisations:
        for _ in range(profile.providers_per_organisation):
            records.append(
                {
                    "provider_id": stable_id("providers", ordinal),
                    "organisation_id": organisation["organisation_id"],
                    "provider_label": f"Provider-{ordinal:06d}",
                    "provider_role": rng.choice(code_sets.PROVIDER_ROLES),
                    "specialty": rng.choice(code_sets.SPECIALTIES),
                    "active_flag": True,
                    "valid_from": iso_date(reference_date - timedelta(days=rng.randint(365, 3650))),
                    "valid_to": None,
                }
            )
            ordinal += 1
    return records


def _patients(
    profile: GenerationProfile, seed: int, reference_date: date, organisations: list[Record]
) -> list[Record]:
    rng = stream(seed, "patients")
    gp_ids = [
        row["organisation_id"] for row in organisations if row["organisation_type"] == "GP_PRACTICE"
    ] or [row["organisation_id"] for row in organisations]
    records: list[Record] = []
    for ordinal in range(1, profile.patient_count + 1):
        patient_id = stable_id("patients", ordinal)
        birth_date = reference_date - timedelta(days=rng.randint(18 * 365, 90 * 365))
        deceased = rng.random() < 0.05
        death_date = None
        if deceased:
            earliest = max(
                birth_date + timedelta(days=18 * 365),
                reference_date - timedelta(days=profile.historical_days),
            )
            death_date = random_date(rng, earliest, reference_date - timedelta(days=1))
        pseudonym = hashlib.sha256(f"{seed}:patient:{ordinal}".encode()).hexdigest()[:20]
        created = max(birth_date, reference_date - timedelta(days=profile.historical_days))
        updated = death_date or reference_date
        records.append(
            {
                "patient_id": patient_id,
                "patient_pseudonym": f"SYN-PSEUDO-{pseudonym}",
                "synthetic_nhs_number": f"SYN-NHS-{ordinal:09d}",
                "birth_date": iso_date(birth_date),
                "sex": rng.choice(code_sets.SEX_CODES),
                "ethnicity": rng.choice(code_sets.ETHNICITY_CODES),
                "postcode_sector": f"SYN-{(ordinal % 40) + 1:02d}",
                "registered_gp_organisation_id": rng.choice(gp_ids),
                "deceased_flag": deceased,
                "death_date": iso_date(death_date) if death_date else None,
                "record_created_at": iso_datetime(at_utc(created)),
                "record_updated_at": iso_datetime(at_utc(updated)),
            }
        )
    return records
