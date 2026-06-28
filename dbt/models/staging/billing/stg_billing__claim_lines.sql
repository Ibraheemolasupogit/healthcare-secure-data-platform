{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'claim_lines') }}

), typed as (

    select
        {{ normalise_empty_string('claim_line_id') }} as claim_line_id,
        {{ normalise_empty_string('claim_id') }} as claim_id,
        {{ normalise_empty_string('billable_activity_id') }} as billable_activity_id,
        {{ normalise_empty_string('service_id') }} as service_id,
        {{ normalise_empty_string('product_id') }} as product_id,
        {{ normalise_empty_string('tariff_id') }} as tariff_id,
        {{ financial_decimal('quantity') }} as quantity,
        {{ financial_decimal('unit_price') }} as unit_price,
        {{ financial_decimal('line_amount') }} as line_amount,
        {{ normalise_code('line_status') }} as line_status,
        {{ normalise_empty_string('rejection_code') }} as rejection_code,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(claim_line_id), '') as source_record_id,
        '{{ source('raw_billing', 'claim_lines') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('claim_line_id', 'source_updated_at desc nulls last, claim_line_id asc') }}

)

select *
from deduplicated
