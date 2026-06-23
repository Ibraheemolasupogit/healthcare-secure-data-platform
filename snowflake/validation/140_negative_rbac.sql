-- EXPECTED-DENIAL PROBES: run one statement at a time and capture the error.
-- A successful statement is a security test failure. Temporary objects avoid persistence.
use role HEDP_DEV_BI_CONSUMER;
create temporary table HEDP_DEV_SERVING.BI.RBAC_NEGATIVE_PROBE (PROBE_ID integer);

use role HEDP_DEV_RESEARCHER;
use database HEDP_DEV_RAW;

use role HEDP_DEV_FINANCE_ANALYST;
use schema HEDP_DEV_RAW.CLINICAL;

use role HEDP_DEV_SERVICE_INGEST;
use schema HEDP_DEV_CURATED.CORE;

use role HEDP_DEV_DATA_ENGINEER;
use database HEDP_PROD_RAW;
