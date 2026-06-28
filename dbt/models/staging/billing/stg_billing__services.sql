{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'services') }}

), typed as (

    select
        {{ normalise_empty_string('service_id') }} as service_id,
        {{ normalise_empty_string('service_code') }} as service_code,
        {{ normalise_empty_string('service_name') }} as service_name,
        {{ normalise_code('service_category') }} as service_category,
        {{ normalise_empty_string('specialty') }} as specialty,
        {{ safe_to_boolean('billable_flag') }} as billable_flag,
        {{ safe_to_boolean('active_flag') }} as active_flag,
        {{ safe_to_date('valid_from') }} as valid_from,
        {{ safe_to_date('valid_to') }} as valid_to,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(service_id), '') as source_record_id,
        '{{ source('raw_billing', 'services') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('service_id', 'source_updated_at desc nulls last, service_id asc') }}

)

select *
from deduplicated
