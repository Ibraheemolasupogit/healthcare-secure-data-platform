{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_quarantine', 'quarantine_records') }}

), typed as (

    select
    {{ normalise_empty_string('quarantine_id') }} as quarantine_id,
    {{ normalise_code('source_format') }} as source_format,
    {{ normalise_empty_string('source_record_id') }} as source_record_id,
    {{ normalise_empty_string('source_message_type') }} as source_message_type,
    validation_errors as validation_errors,
    warning_details as warning_details,
    {{ normalise_empty_string('payload_checksum') }} as payload_checksum,
    {{ normalise_empty_string('raw_payload_path') }} as raw_payload_path,
    {{ normalise_empty_string('retry_eligible') }} as retry_eligible,
    {{ normalise_code('disposition') }} as disposition,
    {{ normalise_empty_string('detected_at') }} as detected_at,
    {{ normalise_empty_string('parser_version') }} as parser_version,
    {{ normalise_empty_string('schema_version') }} as schema_version,
    {{ normalise_empty_string('synthetic_flag') }} as synthetic_flag,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    coalesce(to_varchar(quarantine_id), '') as source_record_id,
    '{{ source('raw_quarantine', 'quarantine_records') }}' as source_relation,
    detected_at as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("quarantine_id", "detected_at desc nulls last, payload_checksum asc, quarantine_id asc") }}

)

select *
from deduplicated
