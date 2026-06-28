{{ config(materialized='ephemeral', tags=['milestone_8', 'billing', 'invoice_calculation']) }}

select
    invoice_id,
    count(*) as invoice_line_count,
    sum(governed_net_amount)::number(18,2) as governed_subtotal_amount,
    sum(governed_tax_amount)::number(18,2) as governed_tax_amount,
    sum(governed_gross_amount)::number(18,2) as governed_total_amount,
    sum(source_net_amount)::number(18,2) as source_line_net_amount,
    sum(source_gross_amount)::number(18,2) as source_line_gross_amount
from {{ ref('int_billing__invoice_line_calculations') }}
group by invoice_id
