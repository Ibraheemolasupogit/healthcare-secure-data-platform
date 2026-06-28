"""Generator orchestration."""

from datetime import date

from healthcare_platform.synthetic.generators.billing import generate_billing
from healthcare_platform.synthetic.generators.care import generate_care
from healthcare_platform.synthetic.generators.foundational import generate_foundational
from healthcare_platform.synthetic.generators.governance import generate_governance
from healthcare_platform.synthetic.generators.types import DatasetMap
from healthcare_platform.synthetic.profiles import GenerationProfile


def generate_all(
    profile: GenerationProfile,
    seed: int,
    reference_date: date,
    inject_defects: bool = False,
    negative_test_mode: bool = False,
) -> DatasetMap:
    """Generate all canonical domains using isolated deterministic streams."""
    data = generate_foundational(profile, seed, reference_date)
    data.update(generate_care(profile, seed, reference_date, data))
    data.update(
        generate_billing(profile, seed, reference_date, data, inject_defects, negative_test_mode)
    )
    data.update(
        generate_governance(profile, seed, reference_date, data, inject_defects, negative_test_mode)
    )
    return data


__all__ = ["generate_all"]
