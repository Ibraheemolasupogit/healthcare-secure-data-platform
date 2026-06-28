-- Milestone 14 static preview only. Do not deploy from this file.
-- Terraform and the Snowflake foundation remain authoritative for durable objects.

-- Example mapping for governance/registry/masking_policies.yaml.
create masking policy if not exists governance.security.m14_mask_direct_identifier_preview
as (value string) returns string ->
    case
        when current_role() in ('BREAK_GLASS_ADMIN') then value
        else 'REDACTED'
    end;

-- Example mapping for governance/registry/row_access_policies.yaml.
create row access policy if not exists governance.security.m14_row_organisation_scope_preview
as (organisation_key string) returns boolean ->
    false; -- default deny until mapped through approved subject-scope tables.
