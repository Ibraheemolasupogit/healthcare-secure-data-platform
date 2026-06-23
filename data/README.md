# Data policy

Only obviously synthetic data is allowed. `raw/` and `synthetic/` outputs are gitignored; small reviewed fixtures may live in `samples/` or `tests/fixtures` beginning in Milestone 2. Every generated dataset will include a manifest with generator version, seed, scale, timestamp, domain counts and an explicit synthetic marker.

Do not place real patient data, NHS numbers, personal data, vendor extracts or production-like secrets here. Large benchmark outputs belong in controlled artefact storage, not Git.
