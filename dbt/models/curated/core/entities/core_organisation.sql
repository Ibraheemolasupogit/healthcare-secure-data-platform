{{ config(materialized='table', tags=['milestone_6', 'core', 'entity']) }}

with organisations as (

    select * from {{ ref('stg_operational__organisations') }}

)

select
    {{ generate_healthcare_surrogate_key(['organisation_id']) }} as organisation_key,
    organisation_id as canonical_organisation_id,
    organisation_code,
    organisation_name,
    organisation_type,
    {{ generate_healthcare_surrogate_key(['parent_organisation_id']) }} as parent_organisation_key,
    parent_organisation_id,
    region,
    active_flag,
    valid_from,
    valid_to,
    {{ current_record_flag('valid_to') }} as is_current,
    source_record_id,
    source_relation,
    source_system,
    synthetic_flag,
    current_timestamp() as dbt_updated_at
from organisations
