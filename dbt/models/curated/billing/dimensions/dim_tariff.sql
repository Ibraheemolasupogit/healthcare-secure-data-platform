{{ config(materialized='table', tags=['milestone_8', 'billing', 'dimension', 'tariff']) }}
select
    {{ generate_healthcare_surrogate_key(['tariffs.tariff_id', 'tariffs.version', 'tariffs.valid_from']) }} as tariff_key,
    tariffs.tariff_id,
    tariffs.tariff_code,
    {{ generate_healthcare_surrogate_key(['tariffs.service_id']) }} as service_key,
    tariffs.service_id,
    {{ generate_healthcare_surrogate_key(['tariffs.product_id']) }} as product_key,
    tariffs.product_id,
    tariffs.payer_type,
    tariffs.specialty,
    tariffs.currency,
    tariffs.unit_price,
    tariffs.valid_from,
    tariffs.valid_to,
    tariffs.version,
    tariffs.active_flag,
    {{ current_record_flag('tariffs.valid_to') }} as is_current,
    tariffs.source_record_id,
    tariffs.source_relation,
    tariffs.source_system,
    tariffs.synthetic_flag,
    current_timestamp() as dbt_updated_at
from {{ ref('stg_billing__tariffs') }} as tariffs
