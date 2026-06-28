{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('governance_control', 'identifier_crosswalks') }}

), typed as (

    select
    {{ normalise_code('source_format') }} as source_format,
    {{ normalise_code('identifier_type') }} as identifier_type,
    {{ normalise_empty_string('source_system') }} as source_system,
    {{ normalise_empty_string('source_identifier') }} as source_identifier,
    {{ normalise_empty_string('canonical_identifier') }} as canonical_identifier,
    {{ normalise_empty_string('mapping_rule_version') }} as mapping_rule_version,
    {{ normalise_code('mapping_status') }} as mapping_status,
    {{ normalise_empty_string('synthetic_flag') }} as synthetic_flag,
    coalesce(to_varchar(source_format), '') || '|' || coalesce(to_varchar(identifier_type), '') || '|' || coalesce(to_varchar(source_identifier), '') as source_record_id,
    '{{ source('governance_control', 'identifier_crosswalks') }}' as source_relation,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("source_format, identifier_type, source_identifier", "source_identifier desc nulls last, source_format asc") }}

)

select *
from deduplicated
