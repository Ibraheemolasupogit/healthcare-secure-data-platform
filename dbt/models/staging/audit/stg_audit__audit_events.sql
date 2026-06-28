{{ config(materialized='view', contract={'enforced': false}, tags=['milestone_5', 'staging', 'source_aligned']) }}

with source_rows as (

    select *
    from {{ source('raw_audit', 'audit_events') }}

), typed as (

    select
    {{ normalise_empty_string('audit_event_id') }} as audit_event_id,
    {{ normalise_empty_string('actor_id') }} as actor_id,
    {{ normalise_empty_string('actor_role') }} as actor_role,
    {{ normalise_empty_string('action') }} as action,
    {{ normalise_empty_string('object_type') }} as object_type,
    {{ normalise_empty_string('object_id') }} as object_id,
    {{ safe_to_timestamp('event_datetime') }} as event_datetime,
    {{ normalise_empty_string('outcome') }} as outcome,
    {{ normalise_empty_string('source_component') }} as source_component,
    {{ normalise_code('environment') }} as environment,
    {{ normalise_empty_string('correlation_id') }} as correlation_id,
    'SYNTHETIC_HEALTHCARE_PLATFORM' as source_system,
    true as synthetic_flag,
    coalesce(to_varchar(audit_event_id), '') as source_record_id,
    '{{ source('raw_audit', 'audit_events') }}' as source_relation,
    event_datetime as source_updated_at,
    current_timestamp() as dbt_loaded_at,
    '{{ invocation_id }}' as dbt_invocation_id,
    false as is_duplicate
    from source_rows

), deduplicated as (

    select *
    from typed
    {{ deduplicate_source("audit_event_id", "event_datetime desc nulls last, audit_event_id asc") }}

)

select *
from deduplicated
