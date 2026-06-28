{{ config(materialized='table', tags=['milestone_8', 'finance', 'fact']) }}
select
    {{ generate_healthcare_surrogate_key(['payments.payment_id']) }} as payment_key,
    {{ generate_healthcare_surrogate_key(['payments.payment_attempt_id']) }} as payment_attempt_key,
    {{ generate_healthcare_surrogate_key(['payments.invoice_id']) }} as invoice_key,
    {{ generate_healthcare_surrogate_key(['payments.payer_id']) }} as payer_key,
    payments.payment_id,
    payments.payment_attempt_id,
    payments.invoice_id,
    payments.payer_id,
    payments.payment_datetime,
    payments.amount,
    payments.currency,
    payments.payment_method,
    payments.payment_status,
    payments.external_reference,
    iff(attempts.payment_attempt_id is null, true, false) as unmatched_attempt_flag,
    iff(attempts.attempt_status != 'SUCCESS', true, false) as non_success_attempt_flag,
    payments.source_record_id,
    payments.source_relation,
    payments.source_system,
    payments.synthetic_flag,
    current_timestamp() as dbt_updated_at
from {{ ref('stg_finance__payments') }} as payments
left join {{ ref('stg_finance__payment_attempts') }} as attempts
    on payments.payment_attempt_id = attempts.payment_attempt_id
