{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_interoperability', 'fhir_raw_payloads') }}

), typed as (

    select
    {{ normalise_empty_string('ingestion_id') }} as ingestion_id,
    {{ normalise_empty_string('resource_type') }} as resource_type,
    {{ normalise_empty_string('resource_id') }} as resource_id,
    payload as payload,
    {{ normalise_empty_string('payload_checksum') }} as payload_checksum,
    {{ normalise_empty_string('received_at') }} as received_at,
    {{ normalise_empty_string('synthetic_flag') }} as synthetic_flag,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    coalesce(to_varchar(ingestion_id), '') as source_record_id,
    '{{ source('raw_interoperability', 'fhir_raw_payloads') }}' as source_relation,
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
