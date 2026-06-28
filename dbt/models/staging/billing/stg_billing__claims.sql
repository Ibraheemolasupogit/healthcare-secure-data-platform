{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'claims') }}

), typed as (

    select
        {{ normalise_empty_string('claim_id') }} as claim_id,
        {{ normalise_empty_string('claim_number') }} as claim_number,
        {{ normalise_empty_string('patient_id') }} as patient_id,
        {{ normalise_empty_string('encounter_id') }} as encounter_id,
        {{ normalise_empty_string('payer_id') }} as payer_id,
        {{ normalise_empty_string('contract_id') }} as contract_id,
        {{ safe_to_date('claim_date') }} as claim_date,
        {{ normalise_empty_string('service_period_start') }} as service_period_start,
        {{ normalise_empty_string('service_period_end') }} as service_period_end,
        {{ normalise_code('claim_status') }} as claim_status,
        {{ normalise_code('currency') }} as currency,
        {{ financial_decimal('claimed_amount') }} as claimed_amount,
        {{ safe_to_timestamp('submitted_at') }} as submitted_at,
        {{ safe_to_timestamp('adjudicated_at') }} as adjudicated_at,
        {{ normalise_empty_string('rejection_code') }} as rejection_code,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(claim_id), '') as source_record_id,
        '{{ source('raw_billing', 'claims') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('claim_id', 'source_updated_at desc nulls last, claim_id asc') }}

)

select *
from deduplicated
