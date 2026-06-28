{{ config(materialized='table', tags=['milestone_6', 'core', 'entity']) }}

with locations as (

    select * from {{ ref('stg_operational__locations') }}

), organisations as (

    select * from {{ ref('core_organisation') }}

)

select
    {{ generate_healthcare_surrogate_key(['locations.location_id']) }} as location_key,
    locations.location_id as canonical_location_id,
    {{ generate_healthcare_surrogate_key(['locations.organisation_id']) }} as organisation_key,
    locations.organisation_id,
    organisations.organisation_type,
    locations.location_code,
    locations.location_name,
    locations.location_type,
    locations.specialty,
    locations.active_flag,
    iff(organisations.organisation_key is null, true, false) as unresolved_organisation_flag,
    locations.source_record_id,
    locations.source_relation,
    locations.source_system,
    locations.synthetic_flag,
    current_timestamp() as dbt_updated_at
from locations
left join organisations
    on locations.organisation_id = organisations.canonical_organisation_id
