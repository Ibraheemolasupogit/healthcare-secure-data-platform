{{ config(materialized='ephemeral', tags=['milestone_9', 'assurance', 'exception']) }}

select
    {{ generate_healthcare_surrogate_key([
        'control.reconciliation_control_key',
        'control.control_rule_id',
        'control.entity_type'
    ]) }} as reconciliation_exception_key,
    control.reconciliation_control_key,
    'RECONCILIATION_FAILURE' as exception_origin,
    case
        when control.record_count_variance != 0 then 'COUNT_VARIANCE'
        when abs(control.amount_variance) > control.tolerance_amount then 'AMOUNT_VARIANCE'
        else 'CONTROL_WARNING'
    end as exception_type,
    control.entity_type as affected_object_type,
    control.entity_type || ':' || to_varchar(control.control_date) as affected_object_id,
    control.reconciliation_control_key as affected_object_key,
    control.source_record_id,
    control.reconciliation_control_key as governed_record_key,
    control.source_amount,
    control.governed_amount,
    control.amount_variance as signed_variance_amount,
    abs(control.amount_variance)::number(18,2) as financial_value_at_risk,
    control.currency,
    control.control_rule_id as rule_id,
    case
        when control.reconciliation_status = 'FAIL' then 'HIGH'
        when control.reconciliation_status = 'WARNING' then 'MEDIUM'
        else 'LOW'
    end as severity,
    control.detected_at,
    control.source_relation,
    control.evidence_reference
from {{ ref('int_assurance__control_results') }} as control
where control.reconciliation_status in ('WARNING', 'FAIL')

union all

select
    {{ generate_healthcare_surrogate_key([
        "'M8_BILLING_EXCEPTION'",
        'billing_exception.exception_type',
        'billing_exception.affected_object_key',
        'billing_exception.detection_rule'
    ]) }} as reconciliation_exception_key,
    cast(null as varchar) as reconciliation_control_key,
    billing_exception.exception_origin,
    billing_exception.exception_type,
    coalesce(split_part(billing_exception.affected_object_id, '-', 1), 'BILLING_OBJECT') as affected_object_type,
    billing_exception.affected_object_id,
    billing_exception.affected_object_key,
    billing_exception.source_record_id,
    billing_exception.affected_object_key as governed_record_key,
    cast(null as number(18,2)) as source_amount,
    cast(null as number(18,2)) as governed_amount,
    cast(null as number(18,2)) as signed_variance_amount,
    coalesce(billing_exception.financial_value_at_risk, 0)::number(18,2) as financial_value_at_risk,
    'GBP' as currency,
    billing_exception.detection_rule as rule_id,
    billing_exception.severity,
    billing_exception.detected_at,
    billing_exception.source_relation,
    billing_exception.billing_exception_key as evidence_reference
from {{ ref('billing_exception') }} as billing_exception
