-- PLANNED, NOT DEPLOYED: evidence-only DDL preview for Milestone 4 raw ingestion contracts.
-- Terraform retains durable container ownership. This file is not in deployment/order.json.
-- No command in this repository executes this preview against Snowflake.

create table if not exists HEDP_DEV_RAW.INTEROPERABILITY.FHIR_RAW_PAYLOADS (
    INGESTION_ID varchar not null,
    RESOURCE_TYPE varchar not null,
    RESOURCE_ID varchar not null,
    PAYLOAD variant not null,
    PAYLOAD_CHECKSUM varchar not null,
    RECEIVED_AT timestamp_tz not null,
    SYNTHETIC_FLAG boolean not null
);

create table if not exists HEDP_DEV_RAW.INTEROPERABILITY.HL7_RAW_MESSAGES (
    INGESTION_ID varchar not null,
    MESSAGE_TYPE varchar not null,
    MESSAGE_CONTROL_ID varchar not null,
    RAW_MESSAGE varchar not null,
    PAYLOAD_CHECKSUM varchar not null,
    RECEIVED_AT timestamp_tz not null,
    SYNTHETIC_FLAG boolean not null
);

create table if not exists HEDP_DEV_RAW.AUDIT.INGESTION_ENVELOPES (
    INGESTION_ID varchar not null,
    BATCH_ID varchar not null,
    SOURCE_FORMAT varchar not null,
    SOURCE_RECORD_ID varchar not null,
    VALIDATION_STATUS varchar not null,
    PAYLOAD_CHECKSUM varchar not null,
    RAW_PAYLOAD_PATH varchar not null,
    SYNTHETIC_FLAG boolean not null
);

create table if not exists HEDP_DEV_RAW.QUARANTINE.QUARANTINE_RECORDS (
    QUARANTINE_ID varchar not null,
    SOURCE_FORMAT varchar not null,
    SOURCE_RECORD_ID varchar not null,
    VALIDATION_ERRORS variant not null,
    PAYLOAD_CHECKSUM varchar not null,
    RAW_PAYLOAD_PATH varchar not null,
    RETRY_ELIGIBLE boolean not null,
    DISPOSITION varchar not null,
    SYNTHETIC_FLAG boolean not null
);

create table if not exists HEDP_DEV_GOVERNANCE.CONTROL.IDENTIFIER_CROSSWALKS (
    SOURCE_FORMAT varchar not null,
    IDENTIFIER_TYPE varchar not null,
    SOURCE_IDENTIFIER varchar not null,
    CANONICAL_IDENTIFIER varchar not null,
    MAPPING_RULE_VERSION varchar not null,
    MAPPING_STATUS varchar not null
);

create table if not exists HEDP_DEV_GOVERNANCE.DATA_QUALITY.VALIDATION_RESULTS (
    INGESTION_ID varchar not null,
    RULE_CODE varchar not null,
    LEVEL varchar not null,
    MESSAGE varchar not null,
    PARSER_VERSION varchar not null,
    SCHEMA_VERSION varchar not null
);
