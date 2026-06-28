{{ config(materialized='table', tags=['milestone_8', 'finance', 'fact']) }}
select
    {{ generate_healthcare_surrogate_key(['payment_attempt_id']) }} as payment_attempt_key,
    {{ generate_healthcare_surrogate_key(['invoice_id']) }} as invoice_key,
    {{ generate_healthcare_surrogate_key(['payer_id']) }} as payer_key,
    payment_attempt_id,
    invoice_id,
    payer_id,
    attempt_datetime,
    payment_method,
    requested_amount,
    attempt_status,
    failure_code,
    gateway_reference,
    idempotency_key,
    case
        when attempt_status = 'FAILED' and failure_code is null then 'FAILED_MISSING_REASON'
        when attempt_status = 'SUCCESS' and failure_code is not null then 'SUCCESS_WITH_FAILURE_REASON'
        else 'CONSISTENT'
    end as attempt_consistency_status,
    source_record_id,
    source_relation,
    source_system,
    synthetic_flag,
    current_timestamp() as dbt_updated_at
from {{ ref('stg_finance__payment_attempts') }}
