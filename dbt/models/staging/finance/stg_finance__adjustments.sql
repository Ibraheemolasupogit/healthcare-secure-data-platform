{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'adjustments') }}

), typed as (

    select
        {{ normalise_empty_string('adjustment_id') }} as adjustment_id,
        {{ normalise_empty_string('invoice_id') }} as invoice_id,
        {{ normalise_empty_string('claim_id') }} as claim_id,
        {{ normalise_code('adjustment_type') }} as adjustment_type,
        {{ normalise_empty_string('adjustment_reason') }} as adjustment_reason,
        {{ safe_to_timestamp('adjustment_datetime') }} as adjustment_datetime,
        {{ financial_decimal('adjustment_amount') }} as adjustment_amount,
        {{ normalise_code('currency') }} as currency,
        {{ normalise_code('status') }} as status,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(adjustment_id), '') as source_record_id,
        '{{ source('raw_billing', 'adjustments') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('adjustment_id', 'source_updated_at desc nulls last, adjustment_id asc') }}

)

select *
from deduplicated
