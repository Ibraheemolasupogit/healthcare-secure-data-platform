{{ config(materialized='table', tags=['milestone_6', 'core', 'entity']) }}

with pathways as (

    select * from {{ ref('stg_operational__pathways') }}

)

select
    {{ generate_healthcare_surrogate_key(['pathway_id']) }} as pathway_key,
    pathway_id as canonical_pathway_id,
    {{ generate_healthcare_surrogate_key(['patient_id']) }} as patient_key,
    patient_id,
    {{ generate_healthcare_surrogate_key(['organisation_id']) }} as organisation_key,
    organisation_id,
    pathway_type,
    specialty,
    referral_date,
    clock_start_date,
    current_status as pathway_status,
    current_stage,
    target_date,
    completion_date,
    waiting_days,
    breach_flag,
    source_record_id,
    source_relation,
    source_system,
    synthetic_flag,
    current_timestamp() as dbt_updated_at
from pathways
