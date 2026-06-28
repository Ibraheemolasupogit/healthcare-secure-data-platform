{{ config(materialized='table', tags=['milestone_9', 'assurance', 'control']) }}

select
    reconciliation_control_key,
    control_date,
    source_system,
    entity_type,
    currency,
    control_rule_id,
    source_record_count,
    governed_record_count,
    record_count_variance,
    source_amount,
    governed_amount,
    amount_variance,
    tolerance_amount,
    tolerance_percentage,
    reconciliation_status,
    timing_difference_flag,
    explanation_code,
    detected_at,
    evidence_reference,
    source_record_id,
    source_relation,
    current_timestamp() as dbt_updated_at
from {{ ref('int_assurance__control_results') }}
