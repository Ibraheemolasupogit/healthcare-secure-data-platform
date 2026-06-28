{{ config(materialized='ephemeral', tags=['milestone_6', 'core', 'identity']) }}

with synthetic_patients as (

    select
        'MILESTONE_2_SYNTHETIC' as source_namespace,
        patient_id as source_patient_identifier,
        patient_id as canonical_patient_id,
        patient_id as source_record_id,
        source_relation,
        source_system,
        source_updated_at,
        '1.0.0' as mapping_version,
        'SYNTHETIC_PRIMARY' as mapping_status,
        false as is_unmatched,
        false as is_conflicting
    from {{ ref('stg_clinical__patients') }}

), interoperability_crosswalks as (

    select
        concat(source_format, ':', source_system) as source_namespace,
        source_identifier as source_patient_identifier,
        canonical_identifier as canonical_patient_id,
        source_record_id,
        source_relation,
        source_system,
        dbt_loaded_at as source_updated_at,
        mapping_rule_version as mapping_version,
        mapping_status,
        iff(canonical_identifier is null, true, false) as is_unmatched,
        false as is_conflicting
    from {{ ref('stg_interoperability__identifier_crosswalks') }}
    where identifier_type = 'PATIENT'

), ingestion_envelope_identifiers as (

    select
        concat(source_format, ':', source_system) as source_namespace,
        source_patient_id as source_patient_identifier,
        coalesce(canonical_patient_id, source_patient_id) as canonical_patient_id,
        source_record_id,
        source_relation,
        source_system,
        received_timestamp as source_updated_at,
        parser_version as mapping_version,
        canonical_mapping_status as mapping_status,
        iff(canonical_patient_id is null and source_patient_id is not null, true, false) as is_unmatched,
        false as is_conflicting
    from {{ ref('stg_interoperability__ingestion_envelopes') }}
    where source_patient_id is not null
      and validation_status in ('ACCEPTED', 'ACCEPTED_WITH_WARNINGS')
      and quarantine_flag = false

), unioned as (

    select * from synthetic_patients
    union all
    select * from interoperability_crosswalks
    union all
    select * from ingestion_envelope_identifiers

), duplicate_conflicts as (

    select
        source_namespace,
        source_patient_identifier,
        count(distinct canonical_patient_id) as canonical_patient_count
    from unioned
    group by source_namespace, source_patient_identifier

)

select
    unioned.source_namespace,
    unioned.source_patient_identifier,
    unioned.canonical_patient_id,
    {{ generate_healthcare_surrogate_key(['unioned.canonical_patient_id']) }} as patient_key,
    unioned.source_record_id,
    unioned.source_relation,
    unioned.source_system,
    unioned.source_updated_at,
    unioned.mapping_version,
    unioned.mapping_status,
    unioned.is_unmatched,
    iff(duplicate_conflicts.canonical_patient_count > 1, true, unioned.is_conflicting) as is_conflicting
from unioned
left join duplicate_conflicts
    on unioned.source_namespace = duplicate_conflicts.source_namespace
    and unioned.source_patient_identifier = duplicate_conflicts.source_patient_identifier
