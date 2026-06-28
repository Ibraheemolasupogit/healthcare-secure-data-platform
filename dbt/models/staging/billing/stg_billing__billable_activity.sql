{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'billable_activity') }}

), typed as (

    select
        {{ normalise_empty_string('billable_activity_id') }} as billable_activity_id,
        {{ normalise_empty_string('patient_id') }} as patient_id,
        {{ normalise_empty_string('encounter_id') }} as encounter_id,
        {{ normalise_empty_string('appointment_id') }} as appointment_id,
        {{ normalise_empty_string('clinical_event_id') }} as clinical_event_id,
        {{ normalise_empty_string('service_id') }} as service_id,
        {{ normalise_empty_string('product_id') }} as product_id,
        {{ normalise_empty_string('provider_id') }} as provider_id,
        {{ normalise_empty_string('organisation_id') }} as organisation_id,
        {{ safe_to_timestamp('activity_datetime') }} as activity_datetime,
        {{ financial_decimal('quantity') }} as quantity,
        {{ normalise_empty_string('unit_of_measure') }} as unit_of_measure,
        {{ normalise_code('billing_status') }} as billing_status,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ normalise_empty_string('source_record_id') }} as source_record_id,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(billable_activity_id), '') as source_record_id,
        '{{ source('raw_billing', 'billable_activity') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('billable_activity_id', 'source_updated_at desc nulls last, billable_activity_id asc') }}

)

select *
from deduplicated
