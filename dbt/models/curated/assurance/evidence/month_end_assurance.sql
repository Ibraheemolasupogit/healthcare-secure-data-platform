{{ config(materialized='table', tags=['milestone_9', 'assurance', 'month_end']) }}

select
    {{ generate_healthcare_surrogate_key([
        "date_trunc('month', control_date)",
        'source_system',
        'currency'
    ]) }} as month_end_assurance_key,
    date_trunc('month', control_date)::date as period_start,
    last_day(control_date)::date as period_end,
    source_system,
    'BILLING_FINANCE_ASSURANCE' as domain,
    currency,
    sum(controls_run) as controls_run,
    sum(controls_passed) as controls_passed,
    sum(controls_failed) as controls_failed,
    sum(unresolved_exception_count) as unresolved_exception_count,
    sum(iff(assurance_status = 'FAIL', unresolved_exception_count, 0)) as overdue_exception_count,
    sum(total_value_at_risk)::number(18,2) as total_value_at_risk,
    0::number(18,2) as resolved_value,
    0::number(18,2) as accepted_risk_value,
    {{ assurance_status_precedence('sum(controls_failed)', 'sum(controls_warned)', 'sum(unresolved_exception_count)') }}
        as assurance_status,
    'M9-MONTH-END-' || to_varchar(date_trunc('month', control_date)::date) || '-' || currency
        as evidence_pack_id,
    current_timestamp() as generated_at
from {{ ref('daily_assurance_summary') }}
group by date_trunc('month', control_date)::date, last_day(control_date)::date, source_system, currency
