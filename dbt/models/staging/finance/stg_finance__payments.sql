{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'payments') }}

), typed as (

    select
        {{ normalise_empty_string('payment_id') }} as payment_id,
        {{ normalise_empty_string('payment_attempt_id') }} as payment_attempt_id,
        {{ normalise_empty_string('invoice_id') }} as invoice_id,
        {{ normalise_empty_string('payer_id') }} as payer_id,
        {{ safe_to_timestamp('payment_datetime') }} as payment_datetime,
        {{ financial_decimal('amount') }} as amount,
        {{ normalise_code('currency') }} as currency,
        {{ normalise_code('payment_method') }} as payment_method,
        {{ normalise_code('payment_status') }} as payment_status,
        {{ normalise_empty_string('external_reference') }} as external_reference,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(payment_id), '') as source_record_id,
        '{{ source('raw_billing', 'payments') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('payment_id', 'source_updated_at desc nulls last, payment_id asc') }}

)

select *
from deduplicated
