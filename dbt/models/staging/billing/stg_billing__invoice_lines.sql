{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_8', 'staging', 'source_aligned', 'billing_finance']) }}

with source_rows as (

    select * from {{ source('raw_billing', 'invoice_lines') }}

), typed as (

    select
        {{ normalise_empty_string('invoice_line_id') }} as invoice_line_id,
        {{ normalise_empty_string('invoice_id') }} as invoice_id,
        {{ normalise_empty_string('billable_activity_id') }} as billable_activity_id,
        {{ normalise_empty_string('claim_line_id') }} as claim_line_id,
        {{ normalise_empty_string('service_id') }} as service_id,
        {{ normalise_empty_string('product_id') }} as product_id,
        {{ normalise_empty_string('tariff_id') }} as tariff_id,
        {{ normalise_empty_string('description') }} as description,
        {{ financial_decimal('quantity') }} as quantity,
        {{ financial_decimal('unit_price') }} as unit_price,
        {{ financial_decimal('net_amount') }} as net_amount,
        {{ financial_decimal('tax_amount') }} as tax_amount,
        {{ financial_decimal('gross_amount') }} as gross_amount,
        {{ normalise_empty_string('source_system') }} as source_system,
        {{ safe_to_timestamp('updated_at') }} as updated_at,
        'SYNTHETIC_BILLING_FINANCE' as source_system_standardised,
        true as synthetic_flag,
        coalesce(to_varchar(invoice_line_id), '') as source_record_id,
        '{{ source('raw_billing', 'invoice_lines') }}' as source_relation,
        updated_at as source_updated_at,
        current_timestamp() as dbt_loaded_at,
        '{{ invocation_id }}' as dbt_invocation_id,
        false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source('invoice_line_id', 'source_updated_at desc nulls last, invoice_line_id asc') }}

)

select *
from deduplicated
