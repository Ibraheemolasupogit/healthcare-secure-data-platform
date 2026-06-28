{{ config(materialized='table', tags=['milestone_6', 'core', 'reconciliation']) }}

select
    {{ generate_healthcare_surrogate_key(['entity_name']) }} as row_count_reconciliation_key,
    entity_name,
    staging_row_count,
    core_row_count,
    staging_row_count - core_row_count as row_count_difference,
    reconciliation_rule,
    iff(staging_row_count = core_row_count, 'BALANCED', 'DIFFERENCE_SURFACED')
        as reconciliation_status,
    current_timestamp() as dbt_updated_at
from {{ ref('int_reconciliation__row_count_differences') }}
