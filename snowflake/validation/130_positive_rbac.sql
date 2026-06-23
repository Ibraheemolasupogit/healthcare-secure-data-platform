-- Run each block in a session allowed to assume the role.
-- These probes verify foundation usage only; no healthcare tables exist yet.
use role HEDP_DEV_ANALYTICS_ENGINEER;
use warehouse HEDP_DEV_TRANSFORM_WH;
use database HEDP_DEV_CURATED;
use schema CORE;
select
    current_role() as ROLE_NAME,
    current_warehouse() as WAREHOUSE_NAME,
    current_database() as DATABASE_NAME,
    current_schema() as SCHEMA_NAME;

use role HEDP_DEV_BI_CONSUMER;
use warehouse HEDP_DEV_BI_WH;
use database HEDP_DEV_SERVING;
use schema BI;
select
    current_role() as ROLE_NAME,
    current_warehouse() as WAREHOUSE_NAME,
    current_database() as DATABASE_NAME,
    current_schema() as SCHEMA_NAME;

use role HEDP_DEV_AUDITOR;
use warehouse HEDP_DEV_ADMIN_WH;
use database HEDP_DEV_GOVERNANCE;
use schema MONITORING;
select
    current_role() as ROLE_NAME,
    current_warehouse() as WAREHOUSE_NAME,
    current_database() as DATABASE_NAME,
    current_schema() as SCHEMA_NAME;
