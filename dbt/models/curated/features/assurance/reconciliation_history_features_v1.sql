{{ config(materialized='table', tags=['milestone_12', 'feature_store', 'assurance_feature']) }}

with controls as (

    select * from {{ ref('reconciliation_control_result') }}

), observations as (

    select distinct
        source_system,
        detected_at as observation_timestamp
    from controls

), feature_rows as (

    select
        observations.source_system as entity_key,
        observations.observation_timestamp,
        observations.observation_timestamp as event_timestamp,
        observations.observation_timestamp as availability_timestamp,
        count(control.reconciliation_control_key) as prior_control_count_30d,
        count_if(control.reconciliation_status = 'FAIL') as prior_control_failure_count_30d,
        (
            count_if(control.reconciliation_status = 'FAIL')
            / nullif(count(control.reconciliation_control_key), 0)
        )::number(18,4) as source_system_failure_rate_30d
    from observations
    left join controls as control
        on observations.source_system = control.source_system
        and control.detected_at < observations.observation_timestamp
        and control.detected_at >= dateadd(day, -30, observations.observation_timestamp)
    group by observations.source_system, observations.observation_timestamp

)

select
    {{ generate_healthcare_surrogate_key([
        "'reconciliation_history_features_v1'",
        'entity_key',
        'observation_timestamp'
    ]) }} as feature_row_key,
    entity_key,
    observation_timestamp,
    event_timestamp,
    availability_timestamp,
    prior_control_count_30d,
    prior_control_failure_count_30d,
    coalesce(source_system_failure_rate_30d, 0)::number(18,4) as source_system_failure_rate_30d,
    'billing_exception_prioritisation_features' as feature_set_id,
    '1.0.0' as feature_set_version,
    iff(prior_control_count_30d = 0, 'NOT_APPLICABLE', 'FRESH') as freshness_status,
    iff(prior_control_count_30d = 0, 'NO_PRIOR_CONTROLS', 'AVAILABLE') as missing_feature_status,
    'reconciliation_control_result' as source_lineage,
    true as synthetic_flag,
    current_timestamp() as dbt_updated_at
from feature_rows
