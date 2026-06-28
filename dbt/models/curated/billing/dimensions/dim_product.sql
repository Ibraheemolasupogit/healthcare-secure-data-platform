{{ config(materialized='table', tags=['milestone_8', 'billing', 'dimension']) }}
select
    {{ generate_healthcare_surrogate_key(['product_id', 'valid_from']) }} as product_key,
    product_id,
    product_code,
    product_name,
    product_category,
    unit_of_measure,
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
from {{ ref('stg_billing__products') }}
