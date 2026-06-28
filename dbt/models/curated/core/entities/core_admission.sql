{{ config(materialized='table', tags=['milestone_6', 'core', 'entity']) }}

with admissions as (

    select * from {{ ref('stg_clinical__admissions') }}

)

select
    {{ generate_healthcare_surrogate_key(['admission_id']) }} as admission_key,
    admission_id as canonical_admission_id,
    {{ generate_healthcare_surrogate_key(['encounter_id']) }} as encounter_key,
    encounter_id,
    {{ generate_healthcare_surrogate_key(['patient_id']) }} as patient_key,
    patient_id,
    {{ generate_healthcare_surrogate_key(['ward_id']) }} as ward_location_key,
    ward_id,
    admission_datetime,
    discharge_datetime,
    admission_method,
    discharge_method,
    length_of_stay_days,
    iff(discharge_datetime is null, true, false) as open_admission_flag,
    readmission_flag,
    prior_admission_id,
    {{ generate_healthcare_surrogate_key(['prior_admission_id']) }} as prior_admission_key,
    source_record_id,
    source_relation,
    source_system,
    synthetic_flag,
    current_timestamp() as dbt_updated_at
from admissions
