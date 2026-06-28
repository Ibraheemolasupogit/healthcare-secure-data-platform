{{ config(materialized='ephemeral', tags=['milestone_8', 'finance', 'payment_allocation']) }}

with payments as (
    select * from {{ ref('stg_finance__payments') }}
), invoices as (
    select invoice_id, total_amount, currency, invoice_date from {{ ref('stg_billing__invoices') }}
)
select
    {{ generate_healthcare_surrogate_key(['payments.payment_id', 'payments.invoice_id']) }} as payment_allocation_key,
    payments.payment_id,
    payments.invoice_id,
    payments.payer_id,
    payments.amount as payment_amount,
    payments.currency,
    invoices.currency as invoice_currency,
    payments.payment_datetime as allocation_datetime,
    iff(invoices.invoice_id is null, true, false) as unmatched_invoice_flag,
    iff(invoices.invoice_id is not null and not {{ currency_compatible('payments.currency', 'invoices.currency') }}, true, false) as currency_mismatch_flag,
    iff(invoices.invoice_id is not null and payments.payment_datetime::date < invoices.invoice_date, true, false) as allocation_precedes_invoice_flag,
    payments.amount as allocated_amount,
    greatest(payments.amount - coalesce(invoices.total_amount, 0), 0)::number(18,2) as unallocated_amount,
    iff(payments.amount > coalesce(invoices.total_amount, 0), true, false) as overpayment_flag,
    case
        when invoices.invoice_id is null then 'UNMATCHED_INVOICE'
        when not {{ currency_compatible('payments.currency', 'invoices.currency') }} then 'CURRENCY_MISMATCH'
        when payments.payment_datetime::date < invoices.invoice_date then 'INVALID_DATE'
        when payments.amount > invoices.total_amount then 'OVERPAYMENT'
        else 'ALLOCATED'
    end as allocation_status
from payments
left join invoices
    on payments.invoice_id = invoices.invoice_id
