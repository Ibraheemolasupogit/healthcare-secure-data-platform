{{ config(materialized='ephemeral', tags=['milestone_9', 'assurance', 'exception']) }}

with exceptions as (

    select * from {{ ref('int_assurance__reconciliation_exceptions') }}

), ownership as (

    select * from {{ ref('assurance_exception_ownership') }}

), severity_rules as (

    select * from {{ ref('assurance_severity_rules') }}

)

select
    exceptions.*,
    coalesce(owner_match.assigned_owner, default_owner.assigned_owner, 'DATA_QUALITY') as assigned_owner,
    coalesce(owner_match.assignment_reason, default_owner.assignment_reason, 'Default assurance owner') as assignment_reason,
    coalesce(owner_match.default_target_resolution_days, default_owner.default_target_resolution_days, 7)
        as target_resolution_days,
    coalesce(owner_match.root_cause_category, default_owner.root_cause_category, 'UNKNOWN') as root_cause,
    coalesce(severity_rules.base_severity, exceptions.severity, 'LOW') as controlled_severity,
    {{ exception_age_days('exceptions.detected_at', "to_date('" ~ var('assurance_as_of_date', '2025-01-01') ~ "')") }}
        as exception_age_days,
    dateadd(day, target_resolution_days, cast(exceptions.detected_at as date)) as target_resolution_date,
    iff(to_date('{{ var("assurance_as_of_date", "2025-01-01") }}') > target_resolution_date, true, false)
        as overdue_flag,
    greatest(datediff(day, target_resolution_date, to_date('{{ var("assurance_as_of_date", "2025-01-01") }}')), 0)
        as days_overdue,
    case
        when exceptions.exception_type in ('HEADER_LINE_MISMATCH', 'AMOUNT_VARIANCE') then 'FINANCIAL_VARIANCE'
        when exceptions.exception_type in ('BALANCE_MISMATCH') then 'BALANCE_VARIANCE'
        when exceptions.exception_type in ('COUNT_VARIANCE') then 'CONTROL_COUNT'
        else 'SOURCE_OR_TRANSFORMATION_EXCEPTION'
    end as exception_group_type,
    {{ generate_healthcare_surrogate_key([
        'exceptions.affected_object_key',
        'exception_group_type',
        'exceptions.currency'
    ]) }} as linked_exception_group_key,
    iff(row_number() over (
        partition by linked_exception_group_key
        order by exceptions.financial_value_at_risk desc, exceptions.rule_id asc
    ) = 1, true, false) as primary_exception_flag,
    primary_exception_flag as include_in_value_at_risk,
    case
        when exceptions.signed_variance_amount is not null then 'DIRECT_VARIANCE'
        when exceptions.financial_value_at_risk > 0 then 'SOURCE_EXCEPTION_VALUE'
        else 'UNKNOWN_OR_ZERO_VALUE'
    end as value_at_risk_method,
    case
        when exceptions.financial_value_at_risk > 0 and exceptions.currency is not null then 'HIGH'
        when exceptions.financial_value_at_risk = 0 then 'LOW'
        else 'UNKNOWN'
    end as value_at_risk_confidence
from exceptions
left join ownership as owner_match
    on exceptions.exception_type = owner_match.exception_type
left join ownership as default_owner
    on default_owner.exception_type = 'DEFAULT'
left join severity_rules
    on exceptions.financial_value_at_risk between severity_rules.minimum_value_at_risk
        and severity_rules.maximum_value_at_risk
