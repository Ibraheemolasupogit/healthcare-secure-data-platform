{{ config(materialized='table', tags=['milestone_8', 'finance', 'fact', 'payment_allocation']) }}
select
    payment_allocation_key,
    {{ generate_healthcare_surrogate_key(['payment_id']) }} as payment_key,
    {{ generate_healthcare_surrogate_key(['invoice_id']) }} as invoice_key,
    payment_id,
    invoice_id,
    payer_id,
    payment_amount,
    allocated_amount,
    unallocated_amount,
    currency,
    invoice_currency,
    allocation_datetime,
    unmatched_invoice_flag,
    currency_mismatch_flag,
    allocation_precedes_invoice_flag,
    overpayment_flag,
    allocation_status,
    current_timestamp() as dbt_updated_at
from {{ ref('int_finance__payment_allocations') }}
