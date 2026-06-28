{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'contracts') }}

), typed as (

    select
        {{ normalise_empty_string('contract_id') }} as contract_id,
        {{ normalise_empty_string('contract_code') }} as contract_code,
        {{ normalise_empty_string('payer_id') }} as payer_id,
        {{ normalise_empty_string('provider_organisation_id') }} as provider_organisation_id,
        {{ normalise_code('contract_type') }} as contract_type,
        {{ safe_to_date('valid_from') }} as valid_from,
        {{ safe_to_date('valid_to') }} as valid_to,
        {{ normalise_code('currency') }} as currency,
        {{ financial_decimal('payment_terms_days') }} as payment_terms_days,
        {{ normalise_code('pricing_basis') }} as pricing_basis,
        {{ normalise_code('status') }} as status,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(contract_id), '') as source_record_id,
        '{{ source('raw_billing', 'contracts') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('contract_id', 'source_updated_at desc nulls last, contract_id asc') }}

)

select *
from deduplicated
