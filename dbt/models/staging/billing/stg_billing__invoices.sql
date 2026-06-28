{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'invoices') }}

), typed as (

    select
        {{ normalise_empty_string('invoice_id') }} as invoice_id,
        {{ normalise_empty_string('invoice_number') }} as invoice_number,
        {{ normalise_empty_string('payer_id') }} as payer_id,
        {{ normalise_empty_string('patient_id') }} as patient_id,
        {{ normalise_empty_string('encounter_id') }} as encounter_id,
        {{ normalise_empty_string('contract_id') }} as contract_id,
        {{ safe_to_date('invoice_date') }} as invoice_date,
        {{ safe_to_date('due_date') }} as due_date,
        {{ normalise_code('invoice_status') }} as invoice_status,
        {{ normalise_code('currency') }} as currency,
        {{ financial_decimal('subtotal_amount') }} as subtotal_amount,
        {{ financial_decimal('tax_amount') }} as tax_amount,
        {{ financial_decimal('total_amount') }} as total_amount,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(invoice_id), '') as source_record_id,
        '{{ source('raw_billing', 'invoices') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('invoice_id', 'source_updated_at desc nulls last, invoice_id asc') }}

)

select *
from deduplicated
