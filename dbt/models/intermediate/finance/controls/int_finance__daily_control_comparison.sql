{{ config(materialized='ephemeral', tags=['milestone_8', 'finance', 'control']) }}

with source_controls as (
    select * from {{ ref('stg_finance__daily_control_totals') }}
), governed as (
    select 'INVOICES' as entity_type, count(*) as governed_record_count, sum(governed_total_amount)::number(18,2) as governed_amount from {{ ref('fct_invoice') }}
    union all
    select 'INVOICE_LINES', count(*), sum(governed_gross_amount)::number(18,2) from {{ ref('fct_invoice_line') }}
    union all
    select 'PAYMENTS', count(*), sum(amount)::number(18,2) from {{ ref('fct_payment') }}
    union all
    select 'REFUNDS', count(*), sum(refund_amount)::number(18,2) from {{ ref('fct_refund') }}
    union all
    select 'ADJUSTMENTS', count(*), sum(adjustment_amount)::number(18,2) from {{ ref('fct_adjustment') }}
)
select
    source_controls.control_total_id,
    source_controls.control_date,
    source_controls.entity_type,
    source_controls.record_count as source_record_count,
    governed.governed_record_count,
    source_controls.gross_amount as source_gross_amount,
    governed.governed_amount,
    (source_controls.record_count - governed.governed_record_count) as record_count_variance,
    round(coalesce(source_controls.gross_amount, 0) - coalesce(governed.governed_amount, 0), 2) as amount_variance,
    case
        when record_count_variance = 0 and abs(amount_variance) <= 0.01 then 'MATCHED'
        else 'VARIANCE'
    end as control_status,
    source_controls.currency,
    source_controls.source_system,
    source_controls.source_record_id,
    source_controls.source_relation,
    source_controls.synthetic_flag,
    current_timestamp() as dbt_updated_at
from source_controls
left join governed
    on source_controls.entity_type = governed.entity_type
