{{ config(materialized='table', tags=['milestone_9', 'assurance', 'revenue_risk']) }}

select
    {{ generate_healthcare_surrogate_key([
        'currency',
        'assigned_owner',
        'priority_band'
    ]) }} as revenue_risk_summary_key,
    currency,
    assigned_owner,
    priority_band,
    count(*) as exception_count,
    sum(iff(include_in_value_at_risk, financial_value_at_risk, 0))::number(18,2)
        as total_value_at_risk,
    sum(iff(include_in_value_at_risk, abs(coalesce(signed_variance_amount, 0)), 0))::number(18,2)
        as signed_variance_abs_total,
    max(severity) as highest_severity,
    count_if(include_in_value_at_risk = false) as secondary_exception_count,
    current_timestamp() as dbt_updated_at
from {{ ref('high_priority_exception_inventory') }}
group by currency, assigned_owner, priority_band
