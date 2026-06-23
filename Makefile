PYTHON ?= python3

.PHONY: install info format lint type test yaml sql dbt-parse terraform-fmt terraform-validate secrets validate

install:
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pip install -e .

info:
	$(PYTHON) -m healthcare_platform.cli info

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

terraform-fmt:
	terraform fmt -check -recursive infrastructure/terraform

terraform-validate:
	terraform -chdir=infrastructure/terraform/environments/dev init -backend=false
	terraform -chdir=infrastructure/terraform/environments/dev validate

secrets:
	@if command -v gitleaks >/dev/null; then gitleaks detect --no-git --redact; else echo "gitleaks not installed; CI performs the authoritative scan"; fi

validate: lint type test yaml sql dbt-parse secrets
	@echo "Core credential-free validation complete. Run terraform-fmt/validate when Terraform is installed."
