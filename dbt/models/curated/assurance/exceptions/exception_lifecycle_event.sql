{{ config(materialized='table', tags=['milestone_9', 'assurance', 'exception_lifecycle']) }}

with exceptions as (

    select * from {{ ref('int_assurance__remediation_state') }}

)

select
    {{ generate_healthcare_surrogate_key([
        'exceptions.reconciliation_exception_key',
        "'OPEN'",
        "'TRIAGED'"
    ]) }} as exception_event_key,
    exceptions.reconciliation_exception_key,
    cast(null as varchar) as previous_status,
    'OPEN' as new_status,
    exceptions.detected_at as event_timestamp,
    'DETECTED' as event_type,
    'SYNTHETIC_ASSURANCE_ENGINE' as actor_role,
    'SYN-ACTOR-DATA-QUALITY' as actor_id,
    exceptions.rule_id as reason_code,
    'SYSTEM_GENERATED' as comment_category,
    exceptions.remediation_action,
    exceptions.evidence_reference,
    'SYN-ASSURANCE' as source_system,
    true as synthetic_flag,
    current_timestamp() as dbt_updated_at
from exceptions

union all

select
    {{ generate_healthcare_surrogate_key([
        'exceptions.reconciliation_exception_key',
        "'OPEN'",
        'exceptions.lifecycle_status'
    ]) }} as exception_event_key,
    exceptions.reconciliation_exception_key,
    'OPEN' as previous_status,
    exceptions.lifecycle_status as new_status,
    dateadd(hour, 1, exceptions.detected_at) as event_timestamp,
    'SYNTHETIC_TRIAGE' as event_type,
    exceptions.assigned_owner as actor_role,
    'SYN-ACTOR-' || exceptions.assigned_owner as actor_id,
    exceptions.root_cause as reason_code,
    'SYNTHETIC_TRIAGE_NOTE' as comment_category,
    exceptions.remediation_action,
    exceptions.evidence_reference,
    'SYN-ASSURANCE' as source_system,
    true as synthetic_flag,
    current_timestamp() as dbt_updated_at
from exceptions
where exceptions.lifecycle_status != 'OPEN'
