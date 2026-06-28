{{ config(materialized='table', tags=['milestone_8', 'billing', 'fact']) }}
with claims as (select * from {{ ref('stg_billing__claims') }}), totals as (select * from {{ ref('int_billing__claim_totals') }})
select
    {{ generate_healthcare_surrogate_key(['claims.claim_id']) }} as claim_key,
    claims.claim_id,
    claims.claim_number,
    patients.patient_key,
    encounters.encounter_key,
    {{ generate_healthcare_surrogate_key(['claims.payer_id']) }} as payer_key,
    {{ generate_healthcare_surrogate_key(['claims.contract_id']) }} as contract_key,
    claims.patient_id,
    claims.encounter_id,
    claims.payer_id,
    claims.contract_id,
    claims.claim_date,
    claims.service_period_start,
    claims.service_period_end,
    claims.claim_status,
    claims.currency,
    claims.claimed_amount as source_claimed_amount,
    coalesce(totals.governed_claim_line_total_amount, 0)::number(18,2) as governed_claim_line_total_amount,
    round(coalesce(claims.claimed_amount, 0) - coalesce(totals.governed_claim_line_total_amount, 0), 2) as claim_variance_amount,
    {{ financial_variance_status('claim_variance_amount') }} as claim_variance_status,
    totals.claim_line_count,
    claims.submitted_at,
    claims.adjudicated_at,
    claims.rejection_code,
    iff(patients.patient_key is null, true, false) as unmatched_patient_flag,
    iff(claims.encounter_id is not null and encounters.encounter_key is null, true, false) as unmatched_encounter_flag,
    claims.source_record_id,
    claims.source_relation,
    claims.source_system,
    claims.synthetic_flag,
    current_timestamp() as dbt_updated_at
from claims
left join totals on claims.claim_id = totals.claim_id
left join {{ ref('core_patient') }} as patients on claims.patient_id = patients.canonical_patient_id
left join {{ ref('core_encounter') }} as encounters on claims.encounter_id = encounters.canonical_encounter_id
