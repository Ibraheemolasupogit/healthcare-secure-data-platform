{{ config(materialized='table', tags=['milestone_6', 'core', 'entity']) }}

with pathology_results as (

    select * from {{ ref('stg_clinical__pathology_results') }}

)

select
    {{ generate_healthcare_surrogate_key(['pathology_result_id']) }} as pathology_result_key,
    pathology_result_id as canonical_pathology_result_id,
    {{ generate_healthcare_surrogate_key(['patient_id']) }} as patient_key,
    patient_id,
    {{ generate_healthcare_surrogate_key(['encounter_id']) }} as encounter_key,
    encounter_id,
    {{ generate_healthcare_surrogate_key(['requesting_provider_id']) }} as requesting_provider_key,
    requesting_provider_id,
    {{ generate_healthcare_surrogate_key(['laboratory_organisation_id']) }}
        as laboratory_organisation_key,
    laboratory_organisation_id,
    test_code,
    test_name,
    result_value,
    result_unit,
    reference_low,
    reference_high,
    abnormal_flag,
    specimen_datetime,
    result_datetime,
    status as result_status,
    source_record_id,
    source_relation,
    source_system,
    synthetic_flag,
    current_timestamp() as dbt_updated_at
from pathology_results
