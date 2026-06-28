{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_finance', 'daily_control_totals') }}

), typed as (

    select
        {{ normalise_empty_string('control_total_id') }} as control_total_id,
        {{ safe_to_date('control_date') }} as control_date,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ normalise_empty_string('entity_type') }} as entity_type,
        {{ financial_decimal('record_count') }} as record_count,
        {{ financial_decimal('gross_amount') }} as gross_amount,
        {{ financial_decimal('net_amount') }} as net_amount,
        {{ financial_decimal('payment_amount') }} as payment_amount,
        {{ financial_decimal('refund_amount') }} as refund_amount,
        {{ financial_decimal('adjustment_amount') }} as adjustment_amount,
        {{ normalise_code('currency') }} as currency,
        {{ safe_to_timestamp('generated_at') }} as generated_at,
        {{ normalise_empty_string('checksum') }} as checksum,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(control_total_id), '') as source_record_id,
        '{{ source('raw_finance', 'daily_control_totals') }}' as source_relation,
        generated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('control_total_id', 'source_updated_at desc nulls last, control_total_id asc') }}

)

select *
from deduplicated
