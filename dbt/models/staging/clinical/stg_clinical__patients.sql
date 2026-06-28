{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_clinical', 'patients') }}

), typed as (

    select
    {{ normalise_empty_string('patient_id') }} as patient_id,
    {{ normalise_empty_string('patient_pseudonym') }} as patient_pseudonym,
    {{ normalise_empty_string('synthetic_nhs_number') }} as synthetic_nhs_number,
    {{ safe_to_date('birth_date') }} as birth_date,
    {{ normalise_code('sex') }} as sex,
    {{ normalise_empty_string('ethnicity') }} as ethnicity,
    {{ normalise_empty_string('postcode_sector') }} as postcode_sector,
    {{ normalise_empty_string('registered_gp_organisation_id') }} as registered_gp_organisation_id,
    {{ safe_to_boolean('deceased_flag') }} as deceased_flag,
    {{ safe_to_date('death_date') }} as death_date,
    {{ safe_to_timestamp('record_created_at') }} as record_created_at,
    {{ safe_to_timestamp('record_updated_at') }} as record_updated_at,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    true as synthetic_flag,
    coalesce(to_varchar(patient_id), '') as source_record_id,
    '{{ source('raw_clinical', 'patients') }}' as source_relation,
    record_updated_at as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("patient_id", "record_updated_at desc nulls last, patient_id asc") }}

)

select *
from deduplicated
