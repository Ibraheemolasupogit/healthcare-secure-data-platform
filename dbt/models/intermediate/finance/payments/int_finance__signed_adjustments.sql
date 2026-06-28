{{ config(materialized='ephemeral', tags=['milestone_8', 'finance', 'adjustment']) }}

select
    adjustments.*,
    {{ calculate_signed_adjustment('adjustments.adjustment_type', 'adjustments.adjustment_amount') }} as signed_adjustment_amount
from {{ ref('stg_finance__adjustments') }} as adjustments
