{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'payment_attempts') }}

), typed as (

    select
        {{ normalise_empty_string('payment_attempt_id') }} as payment_attempt_id,
        {{ normalise_empty_string('invoice_id') }} as invoice_id,
        {{ normalise_empty_string('payer_id') }} as payer_id,
        {{ safe_to_timestamp('attempt_datetime') }} as attempt_datetime,
        {{ normalise_code('payment_method') }} as payment_method,
        {{ financial_decimal('requested_amount') }} as requested_amount,
        {{ normalise_code('attempt_status') }} as attempt_status,
        {{ normalise_empty_string('failure_code') }} as failure_code,
        {{ normalise_empty_string('gateway_reference') }} as gateway_reference,
        {{ normalise_empty_string('idempotency_key') }} as idempotency_key,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(payment_attempt_id), '') as source_record_id,
        '{{ source('raw_billing', 'payment_attempts') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('payment_attempt_id', 'source_updated_at desc nulls last, payment_attempt_id asc') }}

)

select *
from deduplicated
