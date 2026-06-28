{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_finance', 'outstanding_balances') }}

), typed as (

    select
        {{ normalise_empty_string('balance_snapshot_id') }} as balance_snapshot_id,
        {{ normalise_empty_string('invoice_id') }} as invoice_id,
        {{ safe_to_date('snapshot_date') }} as snapshot_date,
        {{ financial_decimal('invoiced_amount') }} as invoiced_amount,
        {{ financial_decimal('payment_amount') }} as payment_amount,
        {{ financial_decimal('refund_amount') }} as refund_amount,
        {{ financial_decimal('adjustment_amount') }} as adjustment_amount,
        {{ financial_decimal('outstanding_amount') }} as outstanding_amount,
        {{ normalise_code('ageing_bucket') }} as ageing_bucket,
        {{ normalise_code('currency') }} as currency,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(balance_snapshot_id), '') as source_record_id,
        '{{ source('raw_finance', 'outstanding_balances') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('balance_snapshot_id', 'source_updated_at desc nulls last, balance_snapshot_id asc') }}

)

select *
from deduplicated
