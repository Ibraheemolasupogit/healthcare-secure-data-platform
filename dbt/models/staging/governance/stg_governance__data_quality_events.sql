{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('governance_data_quality', 'data_quality_events') }}

), typed as (

    select
    {{ normalise_empty_string('quality_event_id') }} as quality_event_id,
    {{ normalise_empty_string('dataset_name') }} as dataset_name,
    {{ normalise_empty_string('rule_id') }} as rule_id,
    {{ normalise_empty_string('rule_name') }} as rule_name,
    {{ normalise_code('severity') }} as severity,
    {{ normalise_empty_string('record_identifier') }} as record_identifier,
    {{ safe_to_timestamp('detected_at') }} as detected_at,
    {{ normalise_code('status') }} as status,
    {{ normalise_empty_string('resolution_action') }} as resolution_action,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    true as synthetic_flag,
    coalesce(to_varchar(quality_event_id), '') as source_record_id,
    '{{ source('governance_data_quality', 'data_quality_events') }}' as source_relation,
    detected_at as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("quality_event_id", "detected_at desc nulls last, quality_event_id asc") }}

)

select *
from deduplicated
