{{ config(materialized='ephemeral', tags=['milestone_9', 'assurance', 'priority']) }}

with exceptions as (

    select * from {{ ref('int_assurance__exception_enriched') }}

), scored as (

    select
        exceptions.*,
        (
            case controlled_severity
                when 'CRITICAL' then 70
                when 'HIGH' then 55
                when 'MEDIUM' then 35
                when 'LOW' then 20
                else 5
            end
            + case
                when financial_value_at_risk >= 10000 then 25
                when financial_value_at_risk >= 1000 then 15
                when financial_value_at_risk >= 100 then 8
                else 0
            end
            + case when overdue_flag then 15 else 0 end
            + least(exception_age_days, 30)
        ) as priority_score
    from exceptions

)

select
    scored.*,
    {{ priority_band('priority_score') }} as priority_band,
    concat(
        controlled_severity,
        ' severity; value at risk ',
        to_varchar(financial_value_at_risk),
        '; age ',
        to_varchar(exception_age_days),
        ' days'
    ) as priority_reason,
    'severity,value_at_risk,age,overdue' as priority_contributing_factors
from scored
