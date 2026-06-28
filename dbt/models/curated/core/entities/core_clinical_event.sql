{{ config(materialized='table', tags=['milestone_6', 'core', 'entity']) }}

with clinical_events as (

    select * from {{ ref('stg_clinical__clinical_events') }}

)

select
    {{ generate_healthcare_surrogate_key(['clinical_event_id']) }} as clinical_event_key,
    clinical_event_id as canonical_clinical_event_id,
    {{ generate_healthcare_surrogate_key(['patient_id']) }} as patient_key,
    patient_id,
    {{ generate_healthcare_surrogate_key(['encounter_id']) }} as encounter_key,
    encounter_id,
    {{ generate_healthcare_surrogate_key(['provider_id']) }} as provider_key,
    provider_id,
    event_type,
    event_code,
    event_value,
    event_unit,
    event_datetime,
    source_record_id,
    source_relation,
    source_system,
    synthetic_flag,
    current_timestamp() as dbt_updated_at
from clinical_events
