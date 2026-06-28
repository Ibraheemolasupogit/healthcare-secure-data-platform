{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_operational', 'organisations') }}

), typed as (

    select
    {{ normalise_empty_string('organisation_id') }} as organisation_id,
    {{ normalise_empty_string('organisation_code') }} as organisation_code,
    {{ normalise_empty_string('organisation_name') }} as organisation_name,
    {{ normalise_code('organisation_type') }} as organisation_type,
    {{ normalise_empty_string('parent_organisation_id') }} as parent_organisation_id,
    {{ normalise_empty_string('region') }} as region,
    {{ safe_to_boolean('active_flag') }} as active_flag,
    {{ safe_to_date('valid_from') }} as valid_from,
    {{ safe_to_date('valid_to') }} as valid_to,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    true as synthetic_flag,
    coalesce(to_varchar(organisation_id), '') as source_record_id,
    '{{ source('raw_operational', 'organisations') }}' as source_relation,
    valid_from as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("organisation_id", "valid_from desc nulls last, organisation_id asc") }}

)

select *
from deduplicated
