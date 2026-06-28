{{ config(materialized='table', tags=['milestone_6', 'core', 'entity']) }}

with encounters as (

    select * from {{ ref('stg_clinical__encounters') }}

), identifier_counts as (

    select
        canonical_encounter_id,
        count(distinct source_namespace) as source_system_count,
        count(*) as source_record_count
    from {{ ref('int_identity__encounter_identifiers') }}
    group by canonical_encounter_id

)

select
    {{ generate_healthcare_surrogate_key(['encounters.encounter_id']) }} as encounter_key,
    encounters.encounter_id as canonical_encounter_id,
    {{ generate_healthcare_surrogate_key(['encounters.patient_id']) }} as patient_key,
    encounters.patient_id,
    {{ generate_healthcare_surrogate_key(['encounters.organisation_id']) }} as organisation_key,
    encounters.organisation_id,
    {{ generate_healthcare_surrogate_key(['encounters.location_id']) }} as location_key,
    encounters.location_id,
    {{ generate_healthcare_surrogate_key(['encounters.provider_id']) }} as provider_key,
    encounters.provider_id,
    encounters.encounter_type,
    encounters.admission_method,
    encounters.start_datetime,
    encounters.end_datetime,
    encounters.status as encounter_status,
    encounters.discharge_destination,
    encounters.primary_diagnosis_code,
    coalesce(identifier_counts.source_system_count, 1) as source_system_count,
    coalesce(identifier_counts.source_record_count, 1) as source_record_count,
    encounters.source_record_id,
    encounters.source_relation,
    encounters.source_system,
    encounters.synthetic_flag,
    current_timestamp() as dbt_updated_at
from encounters
left join identifier_counts
    on encounters.encounter_id = identifier_counts.canonical_encounter_id
