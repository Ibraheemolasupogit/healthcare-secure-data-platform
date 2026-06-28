{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_operational', 'pathways') }}

), typed as (

    select
    {{ normalise_empty_string('pathway_id') }} as pathway_id,
    {{ normalise_empty_string('patient_id') }} as patient_id,
    {{ safe_to_date('referral_date') }} as referral_date,
    {{ normalise_empty_string('pathway_type') }} as pathway_type,
    {{ normalise_empty_string('specialty') }} as specialty,
    {{ normalise_empty_string('organisation_id') }} as organisation_id,
    {{ safe_to_date('clock_start_date') }} as clock_start_date,
    {{ normalise_code('current_status') }} as current_status,
    {{ normalise_empty_string('current_stage') }} as current_stage,
    {{ safe_to_date('target_date') }} as target_date,
    {{ safe_to_date('completion_date') }} as completion_date,
    {{ safe_to_number('waiting_days') }} as waiting_days,
    {{ safe_to_boolean('breach_flag') }} as breach_flag,
    {{ safe_to_timestamp('updated_at') }} as updated_at,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    true as synthetic_flag,
    coalesce(to_varchar(pathway_id), '') as source_record_id,
    '{{ source('raw_operational', 'pathways') }}' as source_relation,
    updated_at as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("pathway_id", "updated_at desc nulls last, pathway_id asc") }}

)

select *
from deduplicated
