PYTHON ?= python3

.PHONY: install info generate-sample validate-sample interoperability-sample interoperability-validate snowflake-inventory snowflake-render snowflake-validate airflow-static dataiku-reference dataiku-static feature-store-reference feature-store-static powerbi-reference powerbi-static format lint type test yaml sql dbt-parse dbt-static terraform-fmt terraform-validate secrets validate

install:
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pip install -e .

info:
	$(PYTHON) -m healthcare_platform.cli info

generate-sample:
	$(PYTHON) -m healthcare_platform.cli generate --profile small --seed 42 --reference-date 2025-01-01 --output-dir data/samples/small --overwrite

validate-sample:
	$(PYTHON) -m healthcare_platform.cli validate-data --input-dir data/samples/small

interoperability-sample:
	$(PYTHON) -m healthcare_platform.cli interoperability process-batch --input-dir data/samples/small/relational --output-dir data/samples/interoperability --seed 42 --overwrite

interoperability-validate:
	$(PYTHON) -m healthcare_platform.cli interoperability validate-fhir --input-dir data/samples/interoperability/fhir
	$(PYTHON) -m healthcare_platform.cli interoperability validate-hl7 --input-dir data/samples/interoperability/hl7
	@! $(PYTHON) -m healthcare_platform.cli interoperability validate-fhir --input-dir data/negative_tests/interoperability/fhir
	@! $(PYTHON) -m healthcare_platform.cli interoperability validate-hl7 --input-dir data/negative_tests/interoperability/hl7

snowflake-inventory:
	$(PYTHON) -m healthcare_platform.cli snowflake-inventory

snowflake-render:
	$(PYTHON) -m healthcare_platform.cli snowflake-render --environment DEV --overwrite

snowflake-validate:
	$(PYTHON) -m healthcare_platform.cli snowflake-validate

format:
	ruff format src tests
	ruff check --fix src tests

lint:
	ruff format --check src tests
	ruff check src tests

type:
	mypy src tests

test:
	pytest --cov --cov-report=term-missing

yaml:
	yamllint . --no-warnings

sql:
	sqlfluff lint snowflake --dialect snowflake

dbt-parse:
	cd dbt && dbt parse --profiles-dir . --no-partial-parse

dbt-static:
	PYTHONPATH=src pytest tests/unit/test_dbt_milestone5.py
	PYTHONPATH=src pytest tests/unit/test_dbt_milestone6.py
	PYTHONPATH=src pytest tests/unit/test_dbt_milestone8.py
	PYTHONPATH=src pytest tests/unit/test_dbt_milestone9.py

airflow-static:
	PYTHONPATH=src pytest tests/unit/test_airflow_milestone10.py

dataiku-reference:
	PYTHONPATH=src $(PYTHON) -m healthcare_platform.cli dataiku-reference --input dataiku/projects/healthcare_analytics/reference_data/billing_exception_analytical_fixture.csv --output-dir dataiku/projects/healthcare_analytics/reference_outputs --overwrite

dataiku-static:
	PYTHONPATH=src pytest tests/unit/test_dataiku_milestone11.py

feature-store-reference:
	PYTHONPATH=src $(PYTHON) -m healthcare_platform.cli feature-store build-reference --output-dir feature_store/reference/outputs --overwrite

feature-store-static:
	PYTHONPATH=src pytest tests/unit/test_feature_store_milestone12.py

powerbi-reference:
	PYTHONPATH=src $(PYTHON) -m healthcare_platform.cli powerbi generate-reference --output-dir powerbi/reference --overwrite
	PYTHONPATH=src $(PYTHON) -m healthcare_platform.cli powerbi verify-reference --output-dir powerbi/reference

powerbi-static:
	PYTHONPATH=src pytest tests/unit/test_powerbi_milestone13.py

terraform-fmt:
	terraform fmt -check -recursive infrastructure/terraform

terraform-validate:
	terraform -chdir=infrastructure/terraform/environments/dev init -backend=false
	terraform -chdir=infrastructure/terraform/environments/dev validate
	terraform -chdir=infrastructure/terraform/environments/test init -backend=false
	terraform -chdir=infrastructure/terraform/environments/test validate
	terraform -chdir=infrastructure/terraform/environments/prod init -backend=false
	terraform -chdir=infrastructure/terraform/environments/prod validate

secrets:
	@if command -v gitleaks >/dev/null; then gitleaks detect --no-git --redact; else echo "gitleaks not installed; CI performs the authoritative scan"; fi

validate: lint type test yaml sql dbt-parse dbt-static airflow-static dataiku-static feature-store-static powerbi-static snowflake-validate interoperability-validate secrets
	@echo "Core credential-free validation complete. Run terraform-fmt/validate when Terraform is installed."
