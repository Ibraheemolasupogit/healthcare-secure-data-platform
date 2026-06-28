{{ config(materialized='table', tags=['milestone_8', 'billing', 'dimension']) }}
select
    {{ generate_healthcare_surrogate_key(['payers.payer_id', 'payers.valid_from']) }} as payer_key,
    payers.payer_id,
    payers.payer_code,
    payers.payer_name,
    payers.payer_type,
    {{ generate_healthcare_surrogate_key(['payers.organisation_id']) }} as linked_organisation_key,
    payers.organisation_id as linked_organisation_id,
    iff(organisations.organisation_key is null and payers.organisation_id is not null, true, false) as unresolved_organisation_flag,
    payers.active_flag,
    payers.valid_from,
    payers.valid_to,
    {{ current_record_flag('payers.valid_to') }} as is_current,
    payers.source_record_id,
    payers.source_relation,
    payers.source_system,
    payers.synthetic_flag,
    current_timestamp() as dbt_updated_at
from {{ ref('stg_billing__payers') }} as payers
left join {{ ref('core_organisation') }} as organisations
    on payers.organisation_id = organisations.canonical_organisation_id
