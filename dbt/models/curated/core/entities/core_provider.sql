{{ config(materialized='table', tags=['milestone_6', 'core', 'entity']) }}

with providers as (

    select * from {{ ref('stg_operational__providers') }}

), organisations as (

    select * from {{ ref('core_organisation') }}

)

select
    {{ generate_healthcare_surrogate_key(['providers.provider_id']) }} as provider_key,
    providers.provider_id as canonical_provider_id,
    {{ generate_healthcare_surrogate_key(['providers.organisation_id']) }} as organisation_key,
    providers.organisation_id,
    providers.provider_label,
    providers.provider_role,
    providers.specialty,
    providers.active_flag,
    providers.valid_from,
    providers.valid_to,
    {{ current_record_flag('providers.valid_to') }} as is_current,
    iff(organisations.organisation_key is null, true, false) as unresolved_organisation_flag,
    providers.source_record_id,
    providers.source_relation,
    providers.source_system,
    providers.synthetic_flag,
    current_timestamp() as dbt_updated_at
from providers
left join organisations
    on providers.organisation_id = organisations.canonical_organisation_id
