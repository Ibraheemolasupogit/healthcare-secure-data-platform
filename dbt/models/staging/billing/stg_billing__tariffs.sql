{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'tariffs') }}

), typed as (

    select
        {{ normalise_empty_string('tariff_id') }} as tariff_id,
        {{ normalise_empty_string('tariff_code') }} as tariff_code,
        {{ normalise_empty_string('service_id') }} as service_id,
        {{ normalise_empty_string('product_id') }} as product_id,
        {{ normalise_code('payer_type') }} as payer_type,
        {{ normalise_empty_string('specialty') }} as specialty,
        {{ normalise_code('currency') }} as currency,
        {{ financial_decimal('unit_price') }} as unit_price,
        {{ safe_to_date('valid_from') }} as valid_from,
        {{ safe_to_date('valid_to') }} as valid_to,
        {{ safe_to_boolean('active_flag') }} as active_flag,
        {{ financial_decimal('version') }} as version,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(tariff_id), '') as source_record_id,
        '{{ source('raw_billing', 'tariffs') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('tariff_id', 'source_updated_at desc nulls last, tariff_id asc') }}

)

select *
from deduplicated
