{{ config(materialized='table', tags=['milestone_6', 'core', 'entity', 'research_foundation']) }}

with patients as (

    select * from {{ ref('core_patient') }}

), cohorts as (

    select * from {{ ref('stg_operational__research_cohorts') }}

)

select
    {{ generate_healthcare_surrogate_key([
        'patients.canonical_patient_id',
        "coalesce(cohorts.cohort_id, 'NO_COHORT')"
    ]) }} as research_eligibility_key,
    patients.patient_key,
    patients.canonical_patient_id,
    cohorts.cohort_membership_id,
    cohorts.cohort_id,
    cohorts.cohort_name,
    patients.research_consent_status,
    cohorts.eligible_flag as cohort_eligible_flag,
    iff(
        patients.research_consent_status = 'ACTIVE'
        and coalesce(cohorts.eligible_flag, false),
        true,
        false
    ) as research_eligible_flag,
    case
        when patients.research_consent_status != 'ACTIVE' then 'NO_ACTIVE_RESEARCH_CONSENT'
        when coalesce(cohorts.eligible_flag, false) = false then 'NO_ELIGIBLE_COHORT'
        else 'ELIGIBLE_SYNTHETIC_RULE'
    end as eligibility_reason_code,
    cohorts.inclusion_date,
    cohorts.exclusion_date,
    cohorts.source_record_id,
    cohorts.source_relation,
    cohorts.source_system,
    cohorts.synthetic_flag,
    current_timestamp() as dbt_updated_at
from patients
left join cohorts
    on patients.canonical_patient_id = cohorts.patient_id
