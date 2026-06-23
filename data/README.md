# Data policy

Only obviously synthetic data is allowed. `raw/`, `synthetic/`, `generated/`, and `negative_tests/` outputs are gitignored. The reviewed lightweight sample lives in `samples/small`. Every generated dataset includes a manifest with generator version, seed, profile, reference date, row counts and an explicit synthetic marker.

Do not place real patient data, NHS numbers, personal data, vendor extracts or production-like secrets here. Large benchmark outputs belong in controlled artefact storage, not Git.
