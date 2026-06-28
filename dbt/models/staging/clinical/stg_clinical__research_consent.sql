{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_clinical', 'research_consent') }}

), typed as (

    select
    {{ normalise_empty_string('consent_id') }} as consent_id,
    {{ normalise_empty_string('patient_id') }} as patient_id,
    {{ normalise_empty_string('consent_type') }} as consent_type,
    {{ normalise_code('consent_status') }} as consent_status,
    {{ safe_to_date('valid_from') }} as valid_from,
    {{ safe_to_date('valid_to') }} as valid_to,
    {{ safe_to_date('withdrawal_date') }} as withdrawal_date,
    {{ safe_to_boolean('research_use_allowed') }} as research_use_allowed,
    {{ safe_to_timestamp('updated_at') }} as updated_at,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    true as synthetic_flag,
    coalesce(to_varchar(consent_id), '') as source_record_id,
    '{{ source('raw_clinical', 'research_consent') }}' as source_relation,
    updated_at as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("consent_id", "updated_at desc nulls last, valid_from desc nulls last, consent_id asc") }}

)

select *
from deduplicated
