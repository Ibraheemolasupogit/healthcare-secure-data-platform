{{ config(materialized='ephemeral', tags=['milestone_9', 'assurance', 'remediation']) }}

with prioritised as (

    select * from {{ ref('int_assurance__exception_priority') }}

)

select
    prioritised.*,
    case
        when controlled_severity in ('CRITICAL', 'HIGH') then 'ASSIGNED'
        when controlled_severity = 'MEDIUM' then 'TRIAGED'
        else 'OPEN'
    end as lifecycle_status,
    cast(detected_at as timestamp_tz) as assigned_at,
    case
        when lifecycle_status in ('ASSIGNED', 'TRIAGED', 'OPEN') then 'PENDING_REVIEW'
        else 'NOT_APPLICABLE'
    end as remediation_status,
    case
        when root_cause = 'PRICING' then 'REVIEW_TARIFF_CONFIGURATION'
        when root_cause = 'CONTRACT' then 'REVIEW_CONTRACT_MAPPING'
        when root_cause = 'PAYMENT' then 'REVIEW_PAYMENT_ALLOCATION'
        when root_cause = 'INVOICE' then 'REVIEW_INVOICE_CONTROL'
        else 'INVESTIGATE_SOURCE_AND_TRANSFORMATION_LINEAGE'
    end as remediation_action,
    cast(null as timestamp_tz) as resolved_at,
    cast(null as varchar) as resolution_code,
    financial_value_at_risk as residual_value_at_risk,
    0 as reopen_count,
    case
        when overdue_flag then 'OVERDUE'
        when exception_age_days <= 7 then '0_7_DAYS'
        when exception_age_days <= 30 then '8_30_DAYS'
        else 'OVER_30_DAYS'
    end as lifecycle_age_band,
    case
        when overdue_flag then 'OVERDUE'
        when lifecycle_status in ('OPEN', 'TRIAGED', 'ASSIGNED') then 'ACTIVE'
        else 'CLOSED'
    end as resolution_status
from prioritised
