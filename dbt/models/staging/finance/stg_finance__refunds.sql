{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'refunds') }}

), typed as (

    select
        {{ normalise_empty_string('refund_id') }} as refund_id,
        {{ normalise_empty_string('payment_id') }} as payment_id,
        {{ normalise_empty_string('invoice_id') }} as invoice_id,
        {{ safe_to_timestamp('refund_datetime') }} as refund_datetime,
        {{ financial_decimal('refund_amount') }} as refund_amount,
        {{ normalise_empty_string('refund_reason') }} as refund_reason,
        {{ normalise_code('refund_status') }} as refund_status,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(refund_id), '') as source_record_id,
        '{{ source('raw_billing', 'refunds') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('refund_id', 'source_updated_at desc nulls last, refund_id asc') }}

)

select *
from deduplicated
