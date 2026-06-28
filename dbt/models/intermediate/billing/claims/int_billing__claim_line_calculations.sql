{{ config(materialized='ephemeral', tags=['milestone_8', 'billing', 'claim_calculation']) }}

with lines as (
    select * from {{ ref('stg_billing__claim_lines') }}
), tariffs as (
    select * from {{ ref('int_billing__selected_tariff') }}
)
select
    lines.*,
    tariffs.selected_tariff_id,
    tariffs.governed_unit_price,
    tariffs.tariff_match_status,
    round(coalesce(lines.quantity, 0) * coalesce(tariffs.governed_unit_price, lines.unit_price, 0), 2) as governed_line_amount,
    round(coalesce(lines.line_amount, 0) - round(coalesce(lines.quantity, 0) * coalesce(tariffs.governed_unit_price, lines.unit_price, 0), 2), 2) as pricing_variance_amount,
    {{ financial_variance_status('pricing_variance_amount') }} as pricing_variance_status
from lines
left join tariffs
    on lines.billable_activity_id = tariffs.billable_activity_id
