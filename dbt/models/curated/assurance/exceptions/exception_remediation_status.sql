{{ config(materialized='table', tags=['milestone_9', 'assurance', 'remediation']) }}

select
    reconciliation_exception_key,
    lifecycle_status,
    assigned_owner,
    assigned_at,
    remediation_status,
    remediation_action,
    root_cause,
    target_resolution_date,
    overdue_flag,
    days_overdue,
    resolved_at,
    resolution_code,
    residual_value_at_risk,
    evidence_reference,
    reopen_count,
    lifecycle_age_band,
    resolution_status,
    current_timestamp() as dbt_updated_at
from {{ ref('int_assurance__remediation_state') }}
