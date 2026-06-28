{{ config(materialized='ephemeral', tags=['milestone_8', 'billing', 'contract_selection']) }}

with invoices as (
    select * from {{ ref('stg_billing__invoices') }}
), contracts as (
    select * from {{ ref('stg_billing__contracts') }}
), candidates as (
    select
        invoices.invoice_id,
        contracts.contract_id,
        contracts.contract_code,
        contracts.currency,
        contracts.payment_terms_days,
        iff(invoices.contract_id = contracts.contract_id, 1, 0) as direct_contract_priority,
        iff(invoices.payer_id = contracts.payer_id, 1, 0) as payer_priority,
        iff(invoices.currency = contracts.currency, 1, 0) as currency_priority,
        iff(invoices.invoice_date between contracts.valid_from and coalesce(contracts.valid_to, to_date('9999-12-31')), 1, 0) as effective_priority,
        iff(contracts.status = 'ACTIVE', 1, 0) as active_priority,
        row_number() over (
            partition by invoices.invoice_id
            order by direct_contract_priority desc, payer_priority desc, currency_priority desc, effective_priority desc, active_priority desc, contracts.contract_id asc
        ) as contract_candidate_rank,
        count(*) over (partition by invoices.invoice_id) as contract_candidate_count
    from invoices
    left join contracts
        on invoices.contract_id = contracts.contract_id
        or invoices.payer_id = contracts.payer_id
)
select
    invoice_id,
    contract_id as selected_contract_id,
    contract_code as selected_contract_code,
    currency as selected_contract_currency,
    payment_terms_days,
    contract_candidate_count,
    case
        when selected_contract_id is null then 'NO_MATCH'
        when currency_priority = 0 then 'CURRENCY_MISMATCH'
        when effective_priority = 0 then 'EXPIRED'
        when active_priority = 0 then 'INACTIVE'
        when contract_candidate_count > 1 and direct_contract_priority = 0 then 'MULTIPLE_MATCHES'
        else 'MATCHED'
    end as contract_match_status,
    case
        when selected_contract_id is null then 'No contract candidate matched payer or contract id.'
        when currency_priority = 0 then 'Selected contract currency differs from invoice currency.'
        when effective_priority = 0 then 'Best contract candidate was outside the invoice date.'
        when active_priority = 0 then 'Best contract candidate was inactive.'
        when contract_candidate_count > 1 and direct_contract_priority = 0 then 'Multiple payer candidates existed; deterministic tie-break applied.'
        else 'Selected by source contract, payer, currency, effective date, active flag and contract id.'
    end as contract_selection_reason
from candidates
where contract_candidate_rank = 1
