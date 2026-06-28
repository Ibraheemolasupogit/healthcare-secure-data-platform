{{ config(materialized='table', tags=['milestone_9', 'assurance', 'exception_inventory']) }}

select *
from {{ ref('reconciliation_exception') }}
where reconciliation_exception_key in (
    select reconciliation_exception_key
    from {{ ref('exception_remediation_status') }}
    where lifecycle_status not in ('RESOLVED', 'ACCEPTED_RISK', 'FALSE_POSITIVE', 'CLOSED')
)
