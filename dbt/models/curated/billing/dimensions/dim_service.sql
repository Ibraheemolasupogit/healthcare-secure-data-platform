{{ config(materialized='table', tags=['milestone_8', 'billing', 'dimension']) }}
select
    {{ generate_healthcare_surrogate_key(['service_id', 'valid_from']) }} as service_key,
    service_id,
    service_code,
    service_name,
    service_category,
    specialty,
    billable_flag,
    active_flag,
    valid_from,
    valid_to,
    {{ current_record_flag('valid_to') }} as is_current,
    source_record_id,
    source_relation,
    source_system,
    synthetic_flag,
    current_timestamp() as dbt_updated_at
from {{ ref('stg_billing__services') }}
