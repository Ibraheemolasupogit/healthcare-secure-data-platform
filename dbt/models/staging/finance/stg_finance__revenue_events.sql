{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_finance', 'revenue_events') }}

), typed as (

    select
        {{ normalise_empty_string('revenue_event_id') }} as revenue_event_id,
        {{ normalise_empty_string('invoice_id') }} as invoice_id,
        {{ normalise_empty_string('invoice_line_id') }} as invoice_line_id,
        {{ normalise_empty_string('claim_id') }} as claim_id,
        {{ normalise_empty_string('billable_activity_id') }} as billable_activity_id,
        {{ normalise_code('event_type') }} as event_type,
        {{ safe_to_timestamp('event_datetime') }} as event_datetime,
        {{ financial_decimal('amount') }} as amount,
        {{ normalise_code('currency') }} as currency,
        {{ normalise_code('source_status') }} as source_status,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(revenue_event_id), '') as source_record_id,
        '{{ source('raw_finance', 'revenue_events') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('revenue_event_id', 'source_updated_at desc nulls last, revenue_event_id asc') }}

)

select *
from deduplicated
