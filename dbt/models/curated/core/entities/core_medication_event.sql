{{ config(materialized='table', tags=['milestone_6', 'core', 'entity']) }}

with medication_events as (

    select * from {{ ref('stg_clinical__medication_events') }}

)

select
    {{ generate_healthcare_surrogate_key(['medication_event_id']) }} as medication_event_key,
    medication_event_id as canonical_medication_event_id,
    {{ generate_healthcare_surrogate_key(['patient_id']) }} as patient_key,
    patient_id,
    {{ generate_healthcare_surrogate_key(['encounter_id']) }} as encounter_key,
    encounter_id,
    {{ generate_healthcare_surrogate_key(['provider_id']) }} as provider_key,
    provider_id,
    medication_code,
    medication_name,
    event_type,
    dose,
    dose_unit,
    route,
    event_datetime,
    status as medication_event_status,
    source_record_id,
    source_relation,
    source_system,
    synthetic_flag,
    current_timestamp() as dbt_updated_at
from medication_events
