{{ config(materialized='table', tags=['milestone_6', 'core', 'identity']) }}

select
    {{ generate_healthcare_surrogate_key(['source_namespace', 'source_patient_identifier']) }}
        as patient_identity_key,
    patient_key,
    canonical_patient_id,
    source_namespace,
    source_patient_identifier,
    source_record_id,
    source_relation,
    source_system,
    source_updated_at,
    mapping_version,
    mapping_status,
    is_unmatched,
    is_conflicting,
    current_timestamp() as dbt_updated_at
from {{ ref('int_identity__patient_identifiers') }}
