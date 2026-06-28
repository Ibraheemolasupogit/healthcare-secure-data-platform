{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_operational', 'research_cohorts') }}

), typed as (

    select
    {{ normalise_empty_string('cohort_membership_id') }} as cohort_membership_id,
    {{ normalise_empty_string('cohort_id') }} as cohort_id,
    {{ normalise_empty_string('patient_id') }} as patient_id,
    {{ normalise_empty_string('cohort_name') }} as cohort_name,
    {{ safe_to_date('inclusion_date') }} as inclusion_date,
    {{ safe_to_date('exclusion_date') }} as exclusion_date,
    {{ normalise_empty_string('inclusion_reason') }} as inclusion_reason,
    {{ safe_to_boolean('eligible_flag') }} as eligible_flag,
    {{ normalise_empty_string('consent_status_at_inclusion') }} as consent_status_at_inclusion,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    true as synthetic_flag,
    coalesce(to_varchar(cohort_membership_id), '') as source_record_id,
    '{{ source('raw_operational', 'research_cohorts') }}' as source_relation,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("cohort_membership_id", "cohort_membership_id asc") }}

)

select *
from deduplicated
