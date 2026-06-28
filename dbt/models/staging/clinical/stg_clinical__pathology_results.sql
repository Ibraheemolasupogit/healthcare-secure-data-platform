{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_clinical', 'pathology_results') }}

), typed as (

    select
    {{ normalise_empty_string('pathology_result_id') }} as pathology_result_id,
    {{ normalise_empty_string('patient_id') }} as patient_id,
    {{ normalise_empty_string('encounter_id') }} as encounter_id,
    {{ normalise_empty_string('requesting_provider_id') }} as requesting_provider_id,
    {{ normalise_empty_string('laboratory_organisation_id') }} as laboratory_organisation_id,
    {{ normalise_empty_string('test_code') }} as test_code,
    {{ normalise_empty_string('test_name') }} as test_name,
    {{ normalise_empty_string('result_value') }} as result_value,
    {{ normalise_empty_string('result_unit') }} as result_unit,
    {{ normalise_empty_string('reference_low') }} as reference_low,
    {{ normalise_empty_string('reference_high') }} as reference_high,
    {{ safe_to_boolean('abnormal_flag') }} as abnormal_flag,
    {{ safe_to_timestamp('specimen_datetime') }} as specimen_datetime,
    {{ safe_to_timestamp('result_datetime') }} as result_datetime,
    {{ normalise_code('status') }} as status,
    {{ safe_to_timestamp('updated_at') }} as updated_at,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    true as synthetic_flag,
    coalesce(to_varchar(pathology_result_id), '') as source_record_id,
    '{{ source('raw_clinical', 'pathology_results') }}' as source_relation,
    updated_at as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("pathology_result_id", "updated_at desc nulls last, result_datetime desc nulls last, pathology_result_id asc") }}

)

select *
from deduplicated
