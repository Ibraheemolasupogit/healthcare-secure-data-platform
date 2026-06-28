{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_clinical', 'medication_events') }}

), typed as (

    select
    {{ normalise_empty_string('medication_event_id') }} as medication_event_id,
    {{ normalise_empty_string('patient_id') }} as patient_id,
    {{ normalise_empty_string('encounter_id') }} as encounter_id,
    {{ normalise_empty_string('provider_id') }} as provider_id,
    {{ normalise_empty_string('medication_code') }} as medication_code,
    {{ normalise_empty_string('medication_name') }} as medication_name,
    {{ normalise_code('event_type') }} as event_type,
    {{ normalise_empty_string('dose') }} as dose,
    {{ normalise_empty_string('dose_unit') }} as dose_unit,
    {{ normalise_empty_string('route') }} as route,
    {{ safe_to_timestamp('event_datetime') }} as event_datetime,
    {{ normalise_code('status') }} as status,
    {{ safe_to_timestamp('updated_at') }} as updated_at,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    true as synthetic_flag,
    coalesce(to_varchar(medication_event_id), '') as source_record_id,
    '{{ source('raw_clinical', 'medication_events') }}' as source_relation,
    updated_at as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("medication_event_id", "updated_at desc nulls last, event_datetime desc nulls last, medication_event_id asc") }}

)

select *
from deduplicated
