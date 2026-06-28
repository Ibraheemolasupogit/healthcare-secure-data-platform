{{ config(materialized='table', tags=['milestone_6', 'core', 'entity']) }}

with patients as (

    select * from {{ ref('stg_clinical__patients') }}

), consent_summary as (

    select
        patient_id,
        max(iff(consent_status = 'ACTIVE' and research_use_allowed, 1, 0)) as active_research_consent,
        max(updated_at) as consent_last_updated_at
    from {{ ref('stg_clinical__research_consent') }}
    group by patient_id

), identity_counts as (

    select
        canonical_patient_id,
        count(distinct source_namespace) as source_system_count,
        count(*) as source_record_count,
        min(source_updated_at) as source_first_seen_at,
        max(source_updated_at) as source_last_seen_at
    from {{ ref('int_identity__patient_identifiers') }}
    group by canonical_patient_id

)

select
    {{ generate_healthcare_surrogate_key(['patients.patient_id']) }} as patient_key,
    patients.patient_id as canonical_patient_id,
    patients.patient_pseudonym,
    patients.synthetic_nhs_number,
    patients.birth_date,
    patients.sex as sex_code,
    patients.ethnicity as ethnicity_code,
    patients.postcode_sector,
    {{ generate_healthcare_surrogate_key(['patients.registered_gp_organisation_id']) }}
        as registered_gp_organisation_key,
    patients.registered_gp_organisation_id,
    patients.deceased_flag,
    patients.death_date,
    iff(consent_summary.active_research_consent = 1, 'ACTIVE', 'NOT_ACTIVE')
        as research_consent_status,
    patients.record_created_at as valid_from,
    cast(null as timestamp_tz) as valid_to,
    true as is_current,
    coalesce(identity_counts.source_system_count, 1) as source_system_count,
    coalesce(identity_counts.source_record_count, 1) as source_record_count,
    coalesce(identity_counts.source_first_seen_at, patients.record_created_at) as source_first_seen_at,
    coalesce(identity_counts.source_last_seen_at, patients.record_updated_at) as source_last_seen_at,
    patients.source_record_id,
    patients.source_relation,
    patients.source_system,
    patients.synthetic_flag,
    current_timestamp() as dbt_updated_at
from patients
left join consent_summary
    on patients.patient_id = consent_summary.patient_id
left join identity_counts
    on patients.patient_id = identity_counts.canonical_patient_id
