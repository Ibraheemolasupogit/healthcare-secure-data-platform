{{ config(materialized='table', tags=['milestone_12', 'feature_store', 'operational_feature']) }}

with appointments as (

    select * from {{ ref('core_appointment') }}

), feature_rows as (

    select
        current_appointment.patient_key as entity_key,
        current_appointment.appointment_datetime as observation_timestamp,
        current_appointment.appointment_datetime as event_timestamp,
        current_appointment.dbt_updated_at as availability_timestamp,
        count(prior_appointment.appointment_key) as prior_appointment_count_180d,
        count_if(prior_appointment.attendance_status = 'DID_NOT_ATTEND')
            as prior_missed_appointment_count_180d,
        avg(datediff(day, prior_appointment.booking_datetime, prior_appointment.appointment_datetime))
            as average_appointment_lead_time_180d
    from appointments as current_appointment
    left join appointments as prior_appointment
        on current_appointment.patient_key = prior_appointment.patient_key
        and prior_appointment.appointment_datetime < current_appointment.appointment_datetime
        and prior_appointment.appointment_datetime
            >= dateadd(day, -180, current_appointment.appointment_datetime)
    group by current_appointment.patient_key, current_appointment.appointment_datetime,
        current_appointment.dbt_updated_at

)

select
    {{ generate_healthcare_surrogate_key([
        "'appointment_history_features_v1'",
        'entity_key',
        'observation_timestamp'
    ]) }} as feature_row_key,
    entity_key,
    observation_timestamp,
    event_timestamp,
    availability_timestamp,
    prior_appointment_count_180d,
    prior_missed_appointment_count_180d,
    coalesce(average_appointment_lead_time_180d, 0)::number(18,2)
        as average_appointment_lead_time_180d,
    'appointment_non_attendance_features_blueprint' as feature_set_id,
    '0.1.0' as feature_set_version,
    iff(prior_appointment_count_180d = 0, 'NOT_APPLICABLE', 'FRESH') as freshness_status,
    iff(prior_appointment_count_180d = 0, 'NO_PRIOR_APPOINTMENTS', 'AVAILABLE')
        as missing_feature_status,
    'core_appointment' as source_lineage,
    true as synthetic_flag,
    current_timestamp() as dbt_updated_at
from feature_rows
