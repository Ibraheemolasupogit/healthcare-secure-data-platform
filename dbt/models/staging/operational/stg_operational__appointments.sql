{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_operational', 'appointments') }}

), typed as (

    select
    {{ normalise_empty_string('appointment_id') }} as appointment_id,
    {{ normalise_empty_string('patient_id') }} as patient_id,
    {{ normalise_empty_string('organisation_id') }} as organisation_id,
    {{ normalise_empty_string('location_id') }} as location_id,
    {{ normalise_empty_string('provider_id') }} as provider_id,
    {{ safe_to_timestamp('appointment_datetime') }} as appointment_datetime,
    {{ safe_to_timestamp('booking_datetime') }} as booking_datetime,
    {{ normalise_code('appointment_type') }} as appointment_type,
    {{ normalise_code('attendance_status') }} as attendance_status,
    {{ normalise_empty_string('cancellation_reason') }} as cancellation_reason,
    {{ normalise_empty_string('referral_id') }} as referral_id,
    {{ safe_to_timestamp('updated_at') }} as updated_at,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    true as synthetic_flag,
    coalesce(to_varchar(appointment_id), '') as source_record_id,
    '{{ source('raw_operational', 'appointments') }}' as source_relation,
    updated_at as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("appointment_id", "updated_at desc nulls last, appointment_datetime desc nulls last, appointment_id asc") }}

)

select *
from deduplicated
