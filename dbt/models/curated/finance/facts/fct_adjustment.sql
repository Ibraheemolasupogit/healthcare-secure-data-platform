{{ config(materialized='table', tags=['milestone_8', 'finance', 'fact']) }}
select
    {{ generate_healthcare_surrogate_key(['adjustment_id']) }} as adjustment_key,
    {{ generate_healthcare_surrogate_key(['invoice_id']) }} as invoice_key,
    {{ generate_healthcare_surrogate_key(['claim_id']) }} as claim_key,
    adjustment_id,
    invoice_id,
    claim_id,
    adjustment_type,
    adjustment_reason,
    adjustment_datetime,
    adjustment_amount,
    signed_adjustment_amount,
    currency,
    status,
    source_record_id,
    source_relation,
    source_system,
    synthetic_flag,
    current_timestamp() as dbt_updated_at
from {{ ref('int_finance__signed_adjustments') }}
