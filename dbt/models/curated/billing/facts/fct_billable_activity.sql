{{ config(materialized='table', tags=['milestone_8', 'billing', 'fact']) }}
with activity as (select * from {{ ref('stg_billing__billable_activity') }}), tariffs as (select * from {{ ref('int_billing__selected_tariff') }})
select
    {{ generate_healthcare_surrogate_key(['activity.billable_activity_id']) }} as billable_activity_key,
    activity.billable_activity_id,
    patients.patient_key,
    encounters.encounter_key,
    appointments.appointment_key,
    clinical_events.clinical_event_key,
    providers.provider_key,
    organisations.organisation_key,
    {{ generate_healthcare_surrogate_key(['activity.service_id']) }} as service_key,
    {{ generate_healthcare_surrogate_key(['activity.product_id']) }} as product_key,
    activity.patient_id,
    activity.encounter_id,
    activity.appointment_id,
    activity.clinical_event_id,
    activity.provider_id,
    activity.organisation_id,
    activity.service_id,
    activity.product_id,
    activity.activity_datetime,
    activity.quantity,
    activity.unit_of_measure,
    activity.billing_status as source_billing_status,
    iff(patients.patient_key is null, true, false) as unmatched_patient_flag,
    iff(activity.encounter_id is not null and encounters.encounter_key is null, true, false) as unmatched_encounter_flag,
    iff(activity.appointment_id is not null and appointments.appointment_key is null, true, false) as unmatched_appointment_flag,
    iff(activity.provider_id is not null and providers.provider_key is null, true, false) as unmatched_provider_flag,
    iff(activity.organisation_id is not null and organisations.organisation_key is null, true, false) as unmatched_organisation_flag,
    tariffs.selected_tariff_id,
    {{ generate_healthcare_surrogate_key(['tariffs.selected_tariff_id']) }} as selected_tariff_key,
    tariffs.tariff_match_status,
    'SOURCE_CONTRACT_MATCHED_AT_INVOICE_GRAIN' as contract_match_status,
    activity.source_record_id,
    activity.source_relation,
    activity.source_system,
    activity.synthetic_flag,
    current_timestamp() as dbt_updated_at
from activity
left join tariffs on activity.billable_activity_id = tariffs.billable_activity_id
left join {{ ref('core_patient') }} as patients on activity.patient_id = patients.canonical_patient_id
left join {{ ref('core_encounter') }} as encounters on activity.encounter_id = encounters.canonical_encounter_id
left join {{ ref('core_appointment') }} as appointments on activity.appointment_id = appointments.canonical_appointment_id
left join {{ ref('core_clinical_event') }} as clinical_events on activity.clinical_event_id = clinical_events.canonical_clinical_event_id
left join {{ ref('core_provider') }} as providers on activity.provider_id = providers.canonical_provider_id
left join {{ ref('core_organisation') }} as organisations on activity.organisation_id = organisations.canonical_organisation_id
