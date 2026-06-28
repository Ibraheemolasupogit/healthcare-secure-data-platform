{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_clinical', 'clinical_events') }}

), typed as (

    select
    {{ normalise_empty_string('clinical_event_id') }} as clinical_event_id,
    {{ normalise_empty_string('patient_id') }} as patient_id,
    {{ normalise_empty_string('encounter_id') }} as encounter_id,
    {{ normalise_empty_string('provider_id') }} as provider_id,
    {{ normalise_code('event_type') }} as event_type,
    {{ normalise_empty_string('event_code') }} as event_code,
    {{ normalise_empty_string('event_value') }} as event_value,
    {{ normalise_empty_string('event_unit') }} as event_unit,
    {{ safe_to_timestamp('event_datetime') }} as event_datetime,
    {{ normalise_empty_string('source_system') }} as source_system,
    {{ safe_to_timestamp('updated_at') }} as updated_at,
    true as synthetic_flag,
    coalesce(to_varchar(clinical_event_id), '') as source_record_id,
    '{{ source('raw_clinical', 'clinical_events') }}' as source_relation,
    updated_at as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("clinical_event_id", "updated_at desc nulls last, event_datetime desc nulls last, clinical_event_id asc") }}

)

select *
from deduplicated
