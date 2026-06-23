-- DEV example for live validation after an explicitly authorised Terraform apply.
-- Render another environment with `healthcare-platform snowflake-render`.
-- noqa: disable=PRS
show databases like 'HEDP_DEV_%';
show schemas like 'HEDP_DEV_%' in account;
show warehouses like 'HEDP_DEV_%';
show resource monitors like 'HEDP_DEV_%';
show roles like 'HEDP_DEV_%';
show tags in account;
