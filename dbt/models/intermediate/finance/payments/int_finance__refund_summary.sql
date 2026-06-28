{{ config(materialized='ephemeral', tags=['milestone_8', 'finance', 'refund']) }}

select
    refunds.payment_id,
    refunds.invoice_id,
    sum(refunds.refund_amount)::number(18,2) as cumulative_refund_amount,
    max(refunds.refund_datetime) as last_refund_datetime
from {{ ref('stg_finance__refunds') }} as refunds
group by refunds.payment_id, refunds.invoice_id
