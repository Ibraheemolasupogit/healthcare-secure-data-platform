{{ config(materialized='table', tags=['milestone_8', 'finance', 'fact']) }}
with refunds as (select * from {{ ref('stg_finance__refunds') }}), payments as (select payment_id, amount, currency, payment_datetime from {{ ref('stg_finance__payments') }}), summaries as (select * from {{ ref('int_finance__refund_summary') }})
select
    {{ generate_healthcare_surrogate_key(['refunds.refund_id']) }} as refund_key,
    {{ generate_healthcare_surrogate_key(['refunds.payment_id']) }} as payment_key,
    {{ generate_healthcare_surrogate_key(['refunds.invoice_id']) }} as invoice_key,
    refunds.refund_id,
    refunds.payment_id,
    refunds.invoice_id,
    refunds.refund_datetime,
    refunds.refund_amount,
    payments.currency,
    refunds.refund_reason,
    refunds.refund_status,
    summaries.cumulative_refund_amount,
    (payments.amount - summaries.cumulative_refund_amount)::number(18,2) as remaining_refundable_amount,
    iff(summaries.cumulative_refund_amount > payments.amount, true, false) as excessive_refund_flag,
    iff(refunds.refund_datetime < payments.payment_datetime, true, false) as refund_precedes_payment_flag,
    refunds.source_record_id,
    refunds.source_relation,
    refunds.source_system,
    refunds.synthetic_flag,
    current_timestamp() as dbt_updated_at
from refunds
left join payments on refunds.payment_id = payments.payment_id
left join summaries on refunds.payment_id = summaries.payment_id and refunds.invoice_id = summaries.invoice_id
