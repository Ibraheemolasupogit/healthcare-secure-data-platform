{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_audit', 'ingestion_envelopes') }}

), typed as (

    select
    {{ normalise_empty_string('ingestion_id') }} as ingestion_id,
    {{ normalise_empty_string('batch_id') }} as batch_id,
    {{ normalise_code('source_format') }} as source_format,
    {{ normalise_empty_string('source_system') }} as source_system,
    {{ normalise_empty_string('source_record_id') }} as source_record_id,
    {{ normalise_empty_string('source_message_type') }} as source_message_type,
    {{ normalise_empty_string('source_patient_id') }} as source_patient_id,
    {{ normalise_empty_string('source_encounter_id') }} as source_encounter_id,
    {{ normalise_empty_string('canonical_patient_id') }} as canonical_patient_id,
    {{ normalise_empty_string('canonical_encounter_id') }} as canonical_encounter_id,
    {{ normalise_code('canonical_mapping_status') }} as canonical_mapping_status,
    {{ normalise_code('validation_status') }} as validation_status,
    {{ normalise_empty_string('validation_error_count') }} as validation_error_count,
    {{ normalise_empty_string('warning_count') }} as warning_count,
    {{ normalise_empty_string('payload_checksum') }} as payload_checksum,
    {{ normalise_empty_string('raw_payload_path') }} as raw_payload_path,
    {{ normalise_empty_string('correlation_id') }} as correlation_id,
    {{ normalise_empty_string('event_timestamp') }} as event_timestamp,
    {{ normalise_empty_string('received_timestamp') }} as received_timestamp,
    {{ normalise_empty_string('parser_version') }} as parser_version,
    {{ normalise_empty_string('schema_version') }} as schema_version,
    {{ normalise_empty_string('payload_version') }} as payload_version,
    {{ normalise_code('environment') }} as environment,
    {{ normalise_empty_string('quarantine_flag') }} as quarantine_flag,
    {{ normalise_empty_string('synthetic_flag') }} as synthetic_flag,
    coalesce(to_varchar(ingestion_id), '') as source_record_id,
    '{{ source('raw_audit', 'ingestion_envelopes') }}' as source_relation,
    received_timestamp as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("ingestion_id", "received_timestamp desc nulls last, batch_id desc nulls last, payload_checksum asc, ingestion_id asc") }}

)

select *
from deduplicated
