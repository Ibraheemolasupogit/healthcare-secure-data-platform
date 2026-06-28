{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('governance_control', 'terminology_mappings') }}

), typed as (

    select
    {{ normalise_empty_string('code_set') }} as code_set,
    {{ normalise_empty_string('source_code') }} as source_code,
    {{ normalise_empty_string('target_code') }} as target_code,
    {{ normalise_code('mapping_status') }} as mapping_status,
    {{ normalise_empty_string('mapping_version') }} as mapping_version,
    {{ normalise_empty_string('synthetic_flag') }} as synthetic_flag,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    coalesce(to_varchar(code_set), '') || '|' || coalesce(to_varchar(source_code), '') as source_record_id,
    '{{ source('governance_control', 'terminology_mappings') }}' as source_relation,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("code_set, source_code", "code_set asc") }}

)

select *
from deduplicated
