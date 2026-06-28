{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('governance_control', 'ingestion_manifests') }}

), typed as (

    select
    {{ normalise_empty_string('batch_id') }} as batch_id,
    {{ normalise_code('source_format') }} as source_format,
    {{ normalise_empty_string('parser_version') }} as parser_version,
    {{ normalise_empty_string('schema_version') }} as schema_version,
    {{ normalise_empty_string('accepted_count') }} as accepted_count,
    {{ normalise_empty_string('rejected_count') }} as rejected_count,
    payload_checksums as payload_checksums,
    {{ normalise_empty_string('synthetic_flag') }} as synthetic_flag,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    coalesce(to_varchar(batch_id), '') || '|' || coalesce(to_varchar(source_format), '') as source_record_id,
    '{{ source('governance_control', 'ingestion_manifests') }}' as source_relation,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("batch_id, source_format", "batch_id desc nulls last, batch_id asc") }}

)

select *
from deduplicated
