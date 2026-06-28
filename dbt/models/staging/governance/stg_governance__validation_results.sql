{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('governance_data_quality', 'validation_results') }}

), typed as (

    select
    {{ normalise_empty_string('ingestion_id') }} as ingestion_id,
    {{ normalise_code('source_format') }} as source_format,
    {{ normalise_empty_string('record_id') }} as record_id,
    {{ normalise_code('message_type') }} as message_type,
    {{ normalise_empty_string('rule_code') }} as rule_code,
    {{ normalise_empty_string('level') }} as level,
    {{ normalise_empty_string('message') }} as message,
    {{ normalise_empty_string('parser_version') }} as parser_version,
    {{ normalise_empty_string('schema_version') }} as schema_version,
    {{ normalise_code('validation_status') }} as validation_status,
    {{ normalise_empty_string('payload_checksum') }} as payload_checksum,
    {{ normalise_empty_string('synthetic_flag') }} as synthetic_flag,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    coalesce(to_varchar(ingestion_id), '') || '|' || coalesce(to_varchar(rule_code), '') as source_record_id,
    '{{ source('governance_data_quality', 'validation_results') }}' as source_relation,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("ingestion_id, rule_code", "payload_checksum asc, ingestion_id asc") }}

)

select *
from deduplicated
