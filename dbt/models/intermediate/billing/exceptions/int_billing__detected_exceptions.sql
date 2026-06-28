{{ config(materialized='ephemeral', tags=['milestone_8', 'billing', 'exception']) }}

with source_exceptions as (
    select
        exception_id,
        exception_type,
        'SOURCE_EXCEPTION' as exception_origin,
        source_record_id as affected_object_id,
        coalesce(invoice_id, claim_id, payment_id, billable_activity_id, source_record_id) as affected_object_key,
        severity,
        financial_value_at_risk,
        status,
        exception_type as detection_rule,
        source_record_id,
        source_relation,
        source_system,
        synthetic_flag,
        detected_at
    from {{ ref('stg_billing__exceptions') }}
), invoice_variances as (
    select
        invoice_id as exception_id,
        'HEADER_LINE_MISMATCH' as exception_type,
        'TRANSFORMATION_DETECTED' as exception_origin,
        invoice_id as affected_object_id,
        invoice_key as affected_object_key,
        'WARNING' as severity,
        abs(header_to_line_variance_amount) as financial_value_at_risk,
        'OPEN' as status,
        'FIN_INV_HEADER_LINE_VARIANCE' as detection_rule,
        source_record_id,
        source_relation,
        source_system,
        synthetic_flag,
        dbt_updated_at as detected_at
    from {{ ref('fct_invoice') }}
    where header_to_line_variance_amount != 0
), balance_variances as (
    select
        balance_snapshot_id as exception_id,
        'BALANCE_MISMATCH' as exception_type,
        'TRANSFORMATION_DETECTED' as exception_origin,
        invoice_id as affected_object_id,
        balance_snapshot_key as affected_object_key,
        'WARNING' as severity,
        abs(source_to_governed_variance_amount) as financial_value_at_risk,
        'OPEN' as status,
        'FIN_BALANCE_VARIANCE' as detection_rule,
        source_record_id,
        source_relation,
        source_system,
        synthetic_flag,
        dbt_updated_at as detected_at
    from {{ ref('fct_outstanding_balance') }}
    where balance_variance_flag
)
select * from source_exceptions
union all
select * from invoice_variances
union all
select * from balance_variances
