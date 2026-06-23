from healthcare_platform.synthetic import code_sets
from healthcare_platform.synthetic.identifiers import PREFIXES, stable_id
from healthcare_platform.synthetic.schemas import DATASET_ORDER, SCHEMAS


def test_all_domains_have_versioned_explicit_schemas() -> None:
    assert len(DATASET_ORDER) == 15
    assert set(DATASET_ORDER) == set(PREFIXES)
    for schema in SCHEMAS.values():
        assert schema.schema_version == "1.0.0"
        assert schema.primary_key
        assert all(field.description and field.classification for field in schema.fields)


def test_stable_identifier_format() -> None:
    assert stable_id("patients", 1) == "PAT-000000001"
    assert stable_id("pathways", 42) == "PTH-000000042"


def test_code_sets_are_nonempty_and_unique() -> None:
    for values in code_sets.ALL_CODE_SETS.values():
        assert values
        assert len(values) == len(set(values))
