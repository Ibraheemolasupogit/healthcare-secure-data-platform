{{ config(materialized='ephemeral', tags=['milestone_8', 'billing', 'claim_calculation']) }}

select
    claim_id,
    count(*) as claim_line_count,
    sum(governed_line_amount)::number(18,2) as governed_claim_line_total_amount,
    sum(line_amount)::number(18,2) as source_claim_line_total_amount
from {{ ref('int_billing__claim_line_calculations') }}
group by claim_id
