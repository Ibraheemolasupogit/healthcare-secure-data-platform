{{ config(materialized='table', tags=['milestone_9', 'assurance', 'evidence_pack']) }}

select
    {{ generate_healthcare_surrogate_key([
        'month_end.evidence_pack_id',
        'month_end.currency'
    ]) }} as assurance_evidence_pack_key,
    month_end.evidence_pack_id,
    month_end.period_start,
    month_end.period_end,
    month_end.source_system,
    month_end.domain,
    month_end.currency,
    month_end.controls_run,
    month_end.controls_passed,
    month_end.controls_failed,
    month_end.unresolved_exception_count,
    month_end.total_value_at_risk,
    month_end.assurance_status,
    'DECLARED_NOT_RUNTIME_PROVEN' as execution_status,
    'dbt_parse_and_static_guardrails' as validation_status,
    'Snowflake execution deferred until authorised credentials are available.' as known_limitations,
    current_timestamp() as generated_at
from {{ ref('month_end_assurance') }} as month_end
