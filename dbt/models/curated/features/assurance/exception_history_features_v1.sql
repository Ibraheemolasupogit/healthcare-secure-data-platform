{{ config(materialized='table', tags=['milestone_12', 'feature_store', 'assurance_feature']) }}

with exceptions as (

    select * from {{ ref('reconciliation_exception') }}

), feature_rows as (

    select
        current_exception.reconciliation_exception_key as entity_key,
        current_exception.detected_at as observation_timestamp,
        current_exception.detected_at as event_timestamp,
        current_exception.detected_at as availability_timestamp,
        count(prior_exception.reconciliation_exception_key) as prior_exception_count_90d,
        count_if(prior_exception.severity in ('HIGH', 'CRITICAL'))
            as prior_high_severity_exception_count_90d,
        coalesce(sum(prior_exception.financial_value_at_risk), 0)::number(18,2)
            as prior_value_at_risk_90d,
        max(prior_exception.detected_at) as latest_source_event_at
    from exceptions as current_exception
    left join exceptions as prior_exception
        on current_exception.affected_object_type = prior_exception.affected_object_type
        and prior_exception.detected_at < current_exception.detected_at
        and prior_exception.detected_at >= dateadd(day, -90, current_exception.detected_at)
    group by
        current_exception.reconciliation_exception_key,
        current_exception.detected_at

)

select
    {{ generate_healthcare_surrogate_key([
        "'exception_history_features_v1'",
        'entity_key',
        'observation_timestamp'
    ]) }} as feature_row_key,
    entity_key,
    observation_timestamp,
    event_timestamp,
    availability_timestamp,
    prior_exception_count_90d,
    prior_high_severity_exception_count_90d,
    prior_value_at_risk_90d,
    'billing_exception_prioritisation_features' as feature_set_id,
    '1.0.0' as feature_set_version,
    iff(latest_source_event_at is null, 'MISSING_HISTORY', 'FRESH') as freshness_status,
    iff(latest_source_event_at is null, 'NO_PRIOR_HISTORY', 'AVAILABLE') as missing_feature_status,
    'reconciliation_exception' as source_lineage,
    true as synthetic_flag,
    current_timestamp() as dbt_updated_at
from feature_rows
