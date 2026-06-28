{{ config(materialized='ephemeral', tags=['milestone_8', 'finance', 'revenue_event']) }}

select
    events.*,
    case
        when event_type in ('BILLED', 'COLLECTED') then amount
        when event_type in ('REFUNDED', 'WRITTEN_OFF') then -1 * amount
        when event_type = 'ADJUSTED' then amount
        else amount
    end::number(18,2) as governed_signed_amount,
    case
        when event_type = 'BILLED' then 'BILLING_LIFECYCLE_EVENT'
        when event_type = 'COLLECTED' then 'CASH_COLLECTION_EVENT'
        when event_type = 'REFUNDED' then 'REFUND_EVENT'
        when event_type = 'ADJUSTED' then 'ADJUSTMENT_EVENT'
        when event_type = 'WRITTEN_OFF' then 'WRITE_OFF_EVENT'
        else 'UNCLASSIFIED_EVENT'
    end as revenue_event_classification
from {{ ref('stg_finance__revenue_events') }} as events
