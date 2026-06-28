{{ config(materialized='table', tags=['milestone_8', 'finance', 'control']) }}
select
    {{ generate_healthcare_surrogate_key(['control_total_id', 'entity_type']) }} as finance_control_key,
    control_total_id,
    control_date,
    entity_type,
    source_record_count,
    governed_record_count,
    source_gross_amount,
    governed_amount,
    record_count_variance,
    amount_variance,
    0.01::number(18,2) as tolerance_amount,
    control_status,
    currency,
    source_system,
    source_record_id,
    source_relation,
    synthetic_flag,
    dbt_updated_at
from {{ ref('int_finance__daily_control_comparison') }}
