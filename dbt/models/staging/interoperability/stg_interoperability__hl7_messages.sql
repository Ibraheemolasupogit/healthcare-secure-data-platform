{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_interoperability', 'hl7_raw_messages') }}

), typed as (

    select
    {{ normalise_empty_string('ingestion_id') }} as ingestion_id,
    {{ normalise_code('message_type') }} as message_type,
    {{ normalise_empty_string('message_control_id') }} as message_control_id,
    raw_message as raw_message,
    {{ normalise_empty_string('payload_checksum') }} as payload_checksum,
    {{ normalise_empty_string('received_at') }} as received_at,
    {{ normalise_empty_string('synthetic_flag') }} as synthetic_flag,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    coalesce(to_varchar(ingestion_id), '') as source_record_id,
    '{{ source('raw_interoperability', 'hl7_raw_messages') }}' as source_relation,
    received_at as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("ingestion_id", "received_at desc nulls last, payload_checksum asc, ingestion_id asc") }}

)

select *
from deduplicated
