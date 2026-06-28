{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'billing_exceptions') }}

), typed as (

    select
        {{ normalise_empty_string('exception_id') }} as exception_id,
        {{ normalise_empty_string('exception_type') }} as exception_type,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ normalise_empty_string('source_record_id') }} as source_record_id,
        {{ normalise_empty_string('patient_id') }} as patient_id,
        {{ normalise_empty_string('encounter_id') }} as encounter_id,
        {{ normalise_empty_string('billable_activity_id') }} as billable_activity_id,
        {{ normalise_empty_string('claim_id') }} as claim_id,
        {{ normalise_empty_string('invoice_id') }} as invoice_id,
        {{ normalise_empty_string('payment_id') }} as payment_id,
        {{ normalise_code('severity') }} as severity,
        {{ financial_decimal('financial_value_at_risk') }} as financial_value_at_risk,
        {{ safe_to_timestamp('detected_at') }} as detected_at,
        {{ normalise_empty_string('assigned_owner') }} as assigned_owner,
        {{ normalise_code('status') }} as status,
        {{ safe_to_date('resolution_date') }} as resolution_date,
        {{ normalise_empty_string('root_cause') }} as root_cause,
        {{ normalise_empty_string('remediation_action') }} as remediation_action,
        {{ safe_to_boolean('synthetic_flag') }} as synthetic_flag,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(exception_id), '') as source_record_id,
        '{{ source('raw_billing', 'billing_exceptions') }}' as source_relation,
        detected_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('exception_id', 'source_updated_at desc nulls last, exception_id asc') }}

)

select *
from deduplicated
