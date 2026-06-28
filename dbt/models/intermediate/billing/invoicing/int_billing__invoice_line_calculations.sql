{{ config(materialized='ephemeral', tags=['milestone_8', 'billing', 'invoice_calculation']) }}

with lines as (
    select * from {{ ref('stg_billing__invoice_lines') }}
), tariffs as (
    select * from {{ ref('int_billing__selected_tariff') }}
)
select
    lines.*,
    tariffs.selected_tariff_id,
    tariffs.governed_unit_price,
    tariffs.tariff_match_status,
    tariffs.tariff_selection_reason,
    round(coalesce(lines.quantity, 0) * coalesce(tariffs.governed_unit_price, lines.unit_price, 0), 2) as governed_net_amount,
    coalesce(lines.tax_amount, 0)::number(18,2) as governed_tax_amount,
    round(coalesce(lines.quantity, 0) * coalesce(tariffs.governed_unit_price, lines.unit_price, 0) + coalesce(lines.tax_amount, 0), 2) as governed_gross_amount,
    lines.net_amount as source_net_amount,
    lines.gross_amount as source_gross_amount,
    round(coalesce(lines.gross_amount, 0) - round(coalesce(lines.quantity, 0) * coalesce(tariffs.governed_unit_price, lines.unit_price, 0) + coalesce(lines.tax_amount, 0), 2), 2) as gross_variance_amount,
    {{ financial_variance_status('gross_variance_amount') }} as gross_variance_status
from lines
left join tariffs
    on lines.billable_activity_id = tariffs.billable_activity_id
