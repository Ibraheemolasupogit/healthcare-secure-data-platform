# Infrastructure delivery boundaries

Terraform remains authoritative for Snowflake foundation infrastructure. GitHub Actions may
run formatting, backend-disabled initialization, validation and plan-contract checks. It
must not embed parallel infrastructure scripts or bypass Terraform ownership.

No live Terraform apply, Snowflake deployment, Dataiku deployment, Airflow deployment,
Fabric/Power BI deployment or GitHub environment administration is claimed by Milestone 15.

