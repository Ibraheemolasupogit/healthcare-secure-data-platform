{{ config(materialized='table', tags=['milestone_6', 'core', 'entity']) }}

with consent as (

    select * from {{ ref('stg_clinical__research_consent') }}

)

select
    {{ generate_healthcare_surrogate_key(['consent_id']) }} as consent_key,
    consent_id as canonical_consent_id,
    {{ generate_healthcare_surrogate_key(['patient_id']) }} as patient_key,
    patient_id,
    consent_type,
    consent_status,
    valid_from,
    valid_to,
    withdrawal_date,
    research_use_allowed,
    {{ current_record_flag('valid_to') }} as is_current,
    source_record_id,
    source_relation,
    source_system,
    synthetic_flag,
    current_timestamp() as dbt_updated_at
from consent
