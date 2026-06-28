{{ config(materialized='table', tags=['milestone_6', 'core', 'reconciliation']) }}

select
    reconciliation_key,
    identifier_type as exception_entity,
    source_identifier as exception_record_id,
    iff(is_conflicting, 'IDENTIFIER_CONFLICT', 'UNMATCHED_IDENTIFIER') as exception_type,
    source_namespace as exception_namespace,
    canonical_identifier,
    source_record_id,
    source_relation,
    current_timestamp() as dbt_updated_at
from {{ ref('int_reconciliation__identifier_conflicts') }}

union all

select
    reconciliation_key,
    source_entity as exception_entity,
    source_record_id as exception_record_id,
    reconciliation_status as exception_type,
    missing_entity as exception_namespace,
    missing_identifier as canonical_identifier,
    source_record_id,
    source_relation,
    dbt_loaded_at as dbt_updated_at
from {{ ref('int_reconciliation__orphan_relationships') }}
