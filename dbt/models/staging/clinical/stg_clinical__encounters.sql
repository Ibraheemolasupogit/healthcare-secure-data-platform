{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_clinical', 'encounters') }}

), typed as (

    select
    {{ normalise_empty_string('encounter_id') }} as encounter_id,
    {{ normalise_empty_string('patient_id') }} as patient_id,
    {{ normalise_empty_string('organisation_id') }} as organisation_id,
    {{ normalise_empty_string('location_id') }} as location_id,
    {{ normalise_empty_string('provider_id') }} as provider_id,
    {{ normalise_code('encounter_type') }} as encounter_type,
    {{ normalise_empty_string('admission_method') }} as admission_method,
    {{ safe_to_timestamp('start_datetime') }} as start_datetime,
    {{ safe_to_timestamp('end_datetime') }} as end_datetime,
    {{ normalise_code('status') }} as status,
    {{ normalise_empty_string('discharge_destination') }} as discharge_destination,
    {{ normalise_empty_string('primary_diagnosis_code') }} as primary_diagnosis_code,
    {{ normalise_empty_string('source_system') }} as source_system,
    {{ safe_to_timestamp('updated_at') }} as updated_at,
    true as synthetic_flag,
    coalesce(to_varchar(encounter_id), '') as source_record_id,
    '{{ source('raw_clinical', 'encounters') }}' as source_relation,
    updated_at as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("encounter_id", "updated_at desc nulls last, encounter_id asc") }}

)

select *
from deduplicated
