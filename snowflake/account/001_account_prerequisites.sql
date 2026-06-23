-- Validation-only prerequisites. Terraform does not create or alter the Snowflake account.
select
    current_organization_name() as ORGANIZATION_NAME,
    current_account_name() as ACCOUNT_NAME,
    current_region() as REGION_NAME,
    current_edition() as EDITION_NAME;

select
    current_user() as USER_NAME,
    current_role() as ROLE_NAME,
    current_warehouse() as WAREHOUSE_NAME;
