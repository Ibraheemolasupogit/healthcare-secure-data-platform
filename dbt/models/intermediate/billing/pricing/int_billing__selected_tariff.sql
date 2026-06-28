{{ config(materialized='ephemeral', tags=['milestone_8', 'billing', 'tariff_selection']) }}

with candidates as (
    select * from {{ ref('int_billing__tariff_candidates') }}
), selected as (
    select * from candidates where tariff_candidate_rank = 1
)
select
    billable_activity_id,
    claim_id,
    tariff_id as selected_tariff_id,
    tariff_code as selected_tariff_code,
    currency as selected_tariff_currency,
    governed_unit_price,
    tariff_candidate_count,
    case
        when selected_tariff_id is null then 'NO_MATCH'
        when effective_priority = 0 then 'EXPIRED'
        when active_priority = 0 then 'INACTIVE'
        when tariff_candidate_count > 1 and product_match_priority = 0 then 'MULTIPLE_MATCHES'
        else 'MATCHED'
    end as tariff_match_status,
    case
        when selected_tariff_id is null then 'No tariff candidate matched source service or product.'
        when effective_priority = 0 then 'Best tariff candidate was outside the source activity date.'
        when active_priority = 0 then 'Best tariff candidate was inactive.'
        when tariff_candidate_count > 1 and product_match_priority = 0 then 'Multiple service-level candidates existed; deterministic tie-break applied.'
        else 'Selected by product/service, effective date, active flag, version and tariff id.'
    end as tariff_selection_reason
from selected
