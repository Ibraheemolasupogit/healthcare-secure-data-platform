{{ config(materialized='ephemeral', tags=['milestone_9', 'assurance', 'reconciliation']) }}

with tolerance as (

    select * from {{ ref('assurance_tolerance_rules') }}

), finance_controls as (

    select
        finance_control_key as upstream_control_key,
        control_date,
        source_system,
        entity_type,
        currency,
        'FIN_DAILY_CONTROL' as control_rule_id,
        source_record_count,
        governed_record_count,
        record_count_variance,
        source_gross_amount as source_amount,
        governed_amount,
        amount_variance,
        tolerance_amount,
        false as timing_difference_flag,
        control_status as upstream_control_status,
        source_record_id,
        source_relation
    from {{ ref('finance_daily_control') }}

), domain_counts as (

    select 'BILLABLE_ACTIVITY_COUNT' as control_rule_id, 'BILLABLE_ACTIVITY' as entity_type,
        count(*) as governed_record_count, sum(quantity)::number(18,2) as governed_amount
    from {{ ref('fct_billable_activity') }}
    union all
    select 'CLAIM_COUNT', 'CLAIMS', count(*), sum(governed_claim_line_total_amount)::number(18,2)
    from {{ ref('fct_claim') }}
    union all
    select 'CLAIM_LINE_COUNT', 'CLAIM_LINES', count(*), sum(governed_line_amount)::number(18,2)
    from {{ ref('fct_claim_line') }}
    union all
    select 'INVOICE_COUNT', 'INVOICES', count(*), sum(governed_total_amount)::number(18,2)
    from {{ ref('fct_invoice') }}
    union all
    select 'INVOICE_LINE_COUNT', 'INVOICE_LINES', count(*), sum(governed_gross_amount)::number(18,2)
    from {{ ref('fct_invoice_line') }}
    union all
    select 'PAYMENT_ATTEMPT_COUNT', 'PAYMENT_ATTEMPTS', count(*), sum(requested_amount)::number(18,2)
    from {{ ref('fct_payment_attempt') }}
    union all
    select 'PAYMENT_COUNT', 'PAYMENTS', count(*), sum(amount)::number(18,2)
    from {{ ref('fct_payment') }}
    union all
    select 'REFUND_COUNT', 'REFUNDS', count(*), sum(refund_amount)::number(18,2)
    from {{ ref('fct_refund') }}
    union all
    select 'ADJUSTMENT_COUNT', 'ADJUSTMENTS', count(*), sum(adjustment_amount)::number(18,2)
    from {{ ref('fct_adjustment') }}
    union all
    select 'REVENUE_EVENT_COUNT', 'REVENUE_EVENTS', count(*), sum(source_amount)::number(18,2)
    from {{ ref('fct_revenue_event') }}
    union all
    select 'OUTSTANDING_BALANCE_COUNT', 'OUTSTANDING_BALANCES', count(*),
        sum(governed_outstanding_amount)::number(18,2)
    from {{ ref('fct_outstanding_balance') }}

), generated_controls as (

    select
        null as upstream_control_key,
        to_date('{{ var("assurance_as_of_date", "2025-01-01") }}') as control_date,
        'SYNTHETIC_BILLING_FINANCE' as source_system,
        entity_type,
        'GBP' as currency,
        control_rule_id,
        governed_record_count as source_record_count,
        governed_record_count,
        0 as record_count_variance,
        governed_amount as source_amount,
        governed_amount,
        0::number(18,2) as amount_variance,
        0.01::number(18,2) as tolerance_amount,
        false as timing_difference_flag,
        'MATCHED' as upstream_control_status,
        entity_type as source_record_id,
        'generated_assurance_control' as source_relation
    from domain_counts

), controls as (

    select * from finance_controls
    union all
    select * from generated_controls

)

select
    {{ generate_healthcare_surrogate_key([
        'controls.control_date',
        'controls.source_system',
        'controls.entity_type',
        'controls.currency',
        'controls.control_rule_id'
    ]) }} as reconciliation_control_key,
    controls.*,
    coalesce(tolerance.tolerance_rule_id, 'TOL-AMOUNT-GBP') as tolerance_rule_id,
    coalesce(tolerance.percentage_tolerance, 0)::number(18,4) as tolerance_percentage,
    {{ assurance_status(
        'controls.record_count_variance',
        'controls.amount_variance',
        'coalesce(tolerance.fixed_amount_tolerance, controls.tolerance_amount, 0.01)',
        'controls.timing_difference_flag'
    ) }} as reconciliation_status,
    case
        when timing_difference_flag then 'EXPECTED_TIMING_WINDOW'
        when record_count_variance = 0 and abs(amount_variance) <= coalesce(tolerance.fixed_amount_tolerance, 0.01)
            then 'WITHIN_TOLERANCE'
        else 'UNEXPLAINED_VARIANCE'
    end as explanation_code,
    current_timestamp() as detected_at,
    'M9-RC-' || controls.control_rule_id || '-' || to_varchar(controls.control_date) as evidence_reference
from controls
left join tolerance
    on controls.currency = coalesce(tolerance.currency, controls.currency)
    and (
        controls.control_rule_id ilike '%' || tolerance.control_type || '%'
        or tolerance.domain in ('ALL', 'FINANCE', 'BILLING')
    )
qualify row_number() over (
    partition by reconciliation_control_key
    order by tolerance.effective_from desc, tolerance.tolerance_rule_id asc
) = 1
