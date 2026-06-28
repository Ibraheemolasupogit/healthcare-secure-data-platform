{{ config(materialized='table', tags=['milestone_8', 'billing', 'fact']) }}
with invoices as (select * from {{ ref('stg_billing__invoices') }}), totals as (select * from {{ ref('int_billing__invoice_totals') }}), contracts as (select * from {{ ref('int_billing__selected_contract') }})
select
    {{ generate_healthcare_surrogate_key(['invoices.invoice_id']) }} as invoice_key,
    invoices.invoice_id,
    invoices.invoice_number,
    {{ generate_healthcare_surrogate_key(['invoices.payer_id']) }} as payer_key,
    patients.patient_key,
    encounters.encounter_key,
    {{ generate_healthcare_surrogate_key(['coalesce(contracts.selected_contract_id, invoices.contract_id)']) }} as contract_key,
    invoices.payer_id,
    invoices.patient_id,
    invoices.encounter_id,
    invoices.contract_id as source_contract_id,
    contracts.selected_contract_id as governed_contract_id,
    contracts.contract_match_status,
    contracts.contract_selection_reason,
    invoices.invoice_date,
    invoices.due_date,
    invoices.invoice_status,
    invoices.currency,
    invoices.subtotal_amount as source_subtotal_amount,
    invoices.tax_amount as source_tax_amount,
    invoices.total_amount as source_total_amount,
    coalesce(totals.governed_subtotal_amount, 0)::number(18,2) as governed_subtotal_amount,
    coalesce(totals.governed_tax_amount, 0)::number(18,2) as governed_tax_amount,
    coalesce(totals.governed_total_amount, 0)::number(18,2) as governed_total_amount,
    round(coalesce(invoices.total_amount, 0) - coalesce(totals.governed_total_amount, 0), 2) as header_to_line_variance_amount,
    {{ financial_variance_status('header_to_line_variance_amount') }} as header_to_line_variance_status,
    totals.invoice_line_count,
    iff(patients.patient_key is null, true, false) as unmatched_patient_flag,
    iff(invoices.encounter_id is not null and encounters.encounter_key is null, true, false) as unmatched_encounter_flag,
    invoices.source_record_id,
    invoices.source_relation,
    invoices.source_system,
    invoices.synthetic_flag,
    current_timestamp() as dbt_updated_at
from invoices
left join totals on invoices.invoice_id = totals.invoice_id
left join contracts on invoices.invoice_id = contracts.invoice_id
left join {{ ref('core_patient') }} as patients on invoices.patient_id = patients.canonical_patient_id
left join {{ ref('core_encounter') }} as encounters on invoices.encounter_id = encounters.canonical_encounter_id
