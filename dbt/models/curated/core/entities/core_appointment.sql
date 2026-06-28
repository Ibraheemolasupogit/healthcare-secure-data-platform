{{ config(materialized='table', tags=['milestone_6', 'core', 'entity']) }}

with appointments as (

    select * from {{ ref('stg_operational__appointments') }}

)

select
    {{ generate_healthcare_surrogate_key(['appointment_id']) }} as appointment_key,
    appointment_id as canonical_appointment_id,
    {{ generate_healthcare_surrogate_key(['patient_id']) }} as patient_key,
    patient_id,
    {{ generate_healthcare_surrogate_key(['organisation_id']) }} as organisation_key,
    organisation_id,
    {{ generate_healthcare_surrogate_key(['location_id']) }} as location_key,
    location_id,
    {{ generate_healthcare_surrogate_key(['provider_id']) }} as provider_key,
    provider_id,
    {{ generate_healthcare_surrogate_key(['referral_id']) }} as referral_event_key,
    referral_id,
    appointment_datetime,
    booking_datetime,
    appointment_type,
    attendance_status,
    cancellation_reason,
    source_record_id,
    source_relation,
    source_system,
    synthetic_flag,
    current_timestamp() as dbt_updated_at
from appointments
