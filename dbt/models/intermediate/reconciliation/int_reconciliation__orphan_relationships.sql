{{ config(materialized='ephemeral', tags=['milestone_6', 'core', 'reconciliation']) }}

with encounter_orphans as (

    select
        'ENCOUNTER' as source_entity,
        encounter_id as source_record_id,
        'PATIENT' as missing_entity,
        patient_id as missing_identifier,
        source_relation
    from {{ ref('stg_clinical__encounters') }} encounters
    left join {{ ref('core_patient') }} patients
        on encounters.patient_id = patients.canonical_patient_id
    where patients.patient_key is null

    union all

    select
        'ENCOUNTER',
        encounter_id,
        'ORGANISATION',
        organisation_id,
        source_relation
    from {{ ref('stg_clinical__encounters') }} encounters
    left join {{ ref('core_organisation') }} organisations
        on encounters.organisation_id = organisations.canonical_organisation_id
    where organisations.organisation_key is null

    union all

    select
        'ENCOUNTER',
        encounter_id,
        'LOCATION',
        location_id,
        source_relation
    from {{ ref('stg_clinical__encounters') }} encounters
    left join {{ ref('core_location') }} locations
        on encounters.location_id = locations.canonical_location_id
    where locations.location_key is null

    union all

    select
        'ENCOUNTER',
        encounter_id,
        'PROVIDER',
        provider_id,
        source_relation
    from {{ ref('stg_clinical__encounters') }} encounters
    left join {{ ref('core_provider') }} providers
        on encounters.provider_id = providers.canonical_provider_id
    where providers.provider_key is null

), appointment_orphans as (

    select
        'APPOINTMENT' as source_entity,
        appointment_id as source_record_id,
        'PATIENT' as missing_entity,
        patient_id as missing_identifier,
        source_relation
    from {{ ref('stg_operational__appointments') }} appointments
    left join {{ ref('core_patient') }} patients
        on appointments.patient_id = patients.canonical_patient_id
    where patients.patient_key is null

), unioned as (

    select * from encounter_orphans
    union all
    select * from appointment_orphans

)

select
    {{ generate_healthcare_surrogate_key([
        'source_entity',
        'source_record_id',
        'missing_entity',
        'missing_identifier'
    ]) }} as reconciliation_key,
    source_entity,
    source_record_id,
    missing_entity,
    missing_identifier,
    source_relation,
    'ORPHAN_REFERENCE' as reconciliation_status,
    current_timestamp() as dbt_loaded_at
from unioned
