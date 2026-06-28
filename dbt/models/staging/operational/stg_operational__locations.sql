{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_operational', 'locations') }}

), typed as (

    select
    {{ normalise_empty_string('location_id') }} as location_id,
    {{ normalise_empty_string('organisation_id') }} as organisation_id,
    {{ normalise_empty_string('location_code') }} as location_code,
    {{ normalise_empty_string('location_name') }} as location_name,
    {{ normalise_code('location_type') }} as location_type,
    {{ normalise_empty_string('specialty') }} as specialty,
    {{ safe_to_boolean('active_flag') }} as active_flag,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    true as synthetic_flag,
    coalesce(to_varchar(location_id), '') as source_record_id,
    '{{ source('raw_operational', 'locations') }}' as source_relation,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("location_id", "location_id asc") }}

)

select *
from deduplicated
