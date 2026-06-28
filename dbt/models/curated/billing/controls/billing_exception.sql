{{ config(materialized='table', tags=['milestone_8', 'billing', 'control', 'exception']) }}
select
    {{ generate_healthcare_surrogate_key(['exception_origin', 'exception_type', 'affected_object_id', 'detection_rule']) }} as billing_exception_key,
    exception_id,
    exception_type,
    exception_origin,
    affected_object_id,
    affected_object_key,
    severity,
    financial_value_at_risk,
    status,
    detection_rule,
    source_record_id,
    source_relation,
    source_system,
    synthetic_flag,
    detected_at,
    current_timestamp() as dbt_updated_at
from {{ ref('int_billing__detected_exceptions') }}
