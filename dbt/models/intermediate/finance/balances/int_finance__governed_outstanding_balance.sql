{{ config(materialized='ephemeral', tags=['milestone_8', 'finance', 'outstanding_balance']) }}

with invoices as (
    select * from {{ ref('fct_invoice') }}
), payments as (
    select invoice_id, sum(allocated_amount)::number(18,2) as valid_allocated_payment_amount from {{ ref('bridge_payment_allocation') }} where allocation_status in ('ALLOCATED', 'OVERPAYMENT') group by invoice_id
), refunds as (
    select invoice_id, sum(refund_amount)::number(18,2) as valid_refund_amount from {{ ref('fct_refund') }} group by invoice_id
), adjustments as (
    select invoice_id, sum(signed_adjustment_amount)::number(18,2) as signed_adjustment_amount from {{ ref('fct_adjustment') }} group by invoice_id
), source_balances as (
    select * from {{ ref('stg_finance__outstanding_balances') }}
)
select
    source_balances.balance_snapshot_id,
    invoices.invoice_id,
    source_balances.snapshot_date,
    invoices.governed_total_amount,
    coalesce(payments.valid_allocated_payment_amount, 0)::number(18,2) as valid_allocated_payment_amount,
    coalesce(refunds.valid_refund_amount, 0)::number(18,2) as valid_refund_amount,
    coalesce(adjustments.signed_adjustment_amount, 0)::number(18,2) as signed_adjustment_amount,
    {{ calculate_outstanding_balance('invoices.governed_total_amount', 'coalesce(payments.valid_allocated_payment_amount, 0)', 'coalesce(refunds.valid_refund_amount, 0)', 'coalesce(adjustments.signed_adjustment_amount, 0)') }} as governed_outstanding_amount,
    source_balances.outstanding_amount as source_outstanding_amount,
    round(source_balances.outstanding_amount - {{ calculate_outstanding_balance('invoices.governed_total_amount', 'coalesce(payments.valid_allocated_payment_amount, 0)', 'coalesce(refunds.valid_refund_amount, 0)', 'coalesce(adjustments.signed_adjustment_amount, 0)') }}, 2) as source_to_governed_variance_amount,
    {{ calculate_ageing_bucket('invoices.due_date', "to_date('{{ var('billing_as_of_date', '2025-01-01') }}')", 'governed_outstanding_amount') }} as governed_ageing_bucket,
    source_balances.ageing_bucket as source_ageing_bucket,
    iff(governed_outstanding_amount < 0, true, false) as credit_balance_flag,
    iff(source_to_governed_variance_amount != 0, true, false) as balance_variance_flag,
    invoices.currency,
    source_balances.source_record_id,
    source_balances.source_relation,
    source_balances.source_system,
    source_balances.synthetic_flag,
    current_timestamp() as dbt_updated_at
from source_balances
left join invoices
    on source_balances.invoice_id = invoices.invoice_id
left join payments
    on source_balances.invoice_id = payments.invoice_id
left join refunds
    on source_balances.invoice_id = refunds.invoice_id
left join adjustments
    on source_balances.invoice_id = adjustments.invoice_id
