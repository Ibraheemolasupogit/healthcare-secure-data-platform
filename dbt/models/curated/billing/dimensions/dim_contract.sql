{{ config(materialized='table', tags=['milestone_8', 'billing', 'dimension', 'contract']) }}
select
    {{ generate_healthcare_surrogate_key(['contracts.contract_id', 'contracts.valid_from']) }} as contract_key,
    contracts.contract_id,
    contracts.contract_code,
    {{ generate_healthcare_surrogate_key(['contracts.payer_id']) }} as payer_key,
    contracts.payer_id,
    {{ generate_healthcare_surrogate_key(['contracts.provider_organisation_id']) }} as provider_organisation_key,
    contracts.provider_organisation_id,
    contracts.contract_type,
    contracts.pricing_basis,
    contracts.payment_terms_days,
    contracts.currency,
    contracts.valid_from,
    contracts.valid_to,
    contracts.status,
    {{ current_record_flag('contracts.valid_to') }} as is_current,
    contracts.source_record_id,
    contracts.source_relation,
    contracts.source_system,
    contracts.synthetic_flag,
    current_timestamp() as dbt_updated_at
from {{ ref('stg_billing__contracts') }} as contracts
