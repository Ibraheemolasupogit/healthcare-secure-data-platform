{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_clinical', 'admissions') }}

), typed as (

    select
    {{ normalise_empty_string('admission_id') }} as admission_id,
    {{ normalise_empty_string('encounter_id') }} as encounter_id,
    {{ normalise_empty_string('patient_id') }} as patient_id,
    {{ safe_to_timestamp('admission_datetime') }} as admission_datetime,
    {{ safe_to_timestamp('discharge_datetime') }} as discharge_datetime,
    {{ normalise_empty_string('admission_method') }} as admission_method,
    {{ normalise_empty_string('discharge_method') }} as discharge_method,
    {{ normalise_empty_string('ward_id') }} as ward_id,
    {{ safe_to_number('length_of_stay_days') }} as length_of_stay_days,
    {{ safe_to_boolean('readmission_flag') }} as readmission_flag,
    {{ normalise_empty_string('prior_admission_id') }} as prior_admission_id,
    {{ safe_to_timestamp('updated_at') }} as updated_at,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    true as synthetic_flag,
    coalesce(to_varchar(admission_id), '') as source_record_id,
    '{{ source('raw_clinical', 'admissions') }}' as source_relation,
    updated_at as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("admission_id", "updated_at desc nulls last, admission_id asc") }}

)

select *
from deduplicated
