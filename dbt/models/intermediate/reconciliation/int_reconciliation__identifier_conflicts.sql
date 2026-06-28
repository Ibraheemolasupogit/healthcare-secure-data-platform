{{ config(materialized='ephemeral', tags=['milestone_6', 'core', 'reconciliation']) }}

with patient_conflicts as (

    select
        'PATIENT' as identifier_type,
        source_namespace,
        source_patient_identifier as source_identifier,
        canonical_patient_id as canonical_identifier,
        source_record_id,
        source_relation,
        is_unmatched,
        is_conflicting
    from {{ ref('int_identity__patient_identifiers') }}
    where is_unmatched = true
       or is_conflicting = true

), encounter_conflicts as (

    select
        'ENCOUNTER' as identifier_type,
        source_namespace,
        source_encounter_identifier as source_identifier,
        canonical_encounter_id as canonical_identifier,
        source_record_id,
        source_relation,
        is_unmatched,
        is_conflicting
    from {{ ref('int_identity__encounter_identifiers') }}
    where is_unmatched = true
       or is_conflicting = true

)

select
    {{ generate_healthcare_surrogate_key([
        'identifier_type',
        'source_namespace',
        'source_identifier',
        "coalesce(canonical_identifier, 'UNMATCHED')"
    ]) }} as reconciliation_key,
    *
from patient_conflicts
union all
select
    {{ generate_healthcare_surrogate_key([
        'identifier_type',
        'source_namespace',
        'source_identifier',
        "coalesce(canonical_identifier, 'UNMATCHED')"
    ]) }} as reconciliation_key,
    *
from encounter_conflicts
