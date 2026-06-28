{{ config(materialized='table', tags=['milestone_9', 'assurance', 'summary']) }}

with controls as (

    select * from {{ ref('reconciliation_control_result') }}

), exceptions as (

    select * from {{ ref('open_exception_inventory') }}

)

select
    {{ generate_healthcare_surrogate_key([
        'controls.control_date',
        'controls.source_system',
        'controls.currency'
    ]) }} as daily_assurance_summary_key,
    controls.control_date,
    controls.source_system,
    controls.currency,
    count(*) as controls_run,
    count_if(controls.reconciliation_status = 'PASS') as controls_passed,
    count_if(controls.reconciliation_status = 'WARNING') as controls_warned,
    count_if(controls.reconciliation_status = 'FAIL') as controls_failed,
    count(distinct exceptions.reconciliation_exception_key) as unresolved_exception_count,
    coalesce(sum(iff(exceptions.include_in_value_at_risk, exceptions.financial_value_at_risk, 0)), 0)::number(18,2)
        as total_value_at_risk,
    max(exceptions.severity) as highest_severity,
    {{ assurance_status_precedence('controls_failed', 'controls_warned', 'unresolved_exception_count') }}
        as assurance_status,
    'M9-DAILY-' || to_varchar(controls.control_date) || '-' || controls.currency as evidence_pack_reference,
    current_timestamp() as dbt_updated_at
from controls
left join exceptions
    on controls.currency = exceptions.currency
group by controls.control_date, controls.source_system, controls.currency
