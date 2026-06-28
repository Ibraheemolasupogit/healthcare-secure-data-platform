{{ config(materialized='table', tags=['milestone_9', 'assurance', 'exception_inventory']) }}

select
    exceptions.*,
    priority.priority_score,
    priority.priority_band,
    priority.priority_reason,
    priority.priority_contributing_factors
from {{ ref('reconciliation_exception') }} as exceptions
inner join {{ ref('int_assurance__exception_priority') }} as priority
    on exceptions.reconciliation_exception_key = priority.reconciliation_exception_key
where priority.priority_band in ('P1', 'P2')
