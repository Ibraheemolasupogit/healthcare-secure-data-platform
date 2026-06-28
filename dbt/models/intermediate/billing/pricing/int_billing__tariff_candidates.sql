{{ config(materialized='ephemeral', tags=['milestone_8', 'billing', 'tariff_selection']) }}

with activity as (
    select * from {{ ref('stg_billing__billable_activity') }}
), tariffs as (
    select * from {{ ref('stg_billing__tariffs') }}
), claims as (
    select billable_activity_id, max(claim_id) as claim_id from {{ ref('stg_billing__claim_lines') }} group by billable_activity_id
)
select
    activity.billable_activity_id,
    claims.claim_id,
    tariffs.tariff_id,
    tariffs.tariff_code,
    tariffs.currency,
    tariffs.unit_price as governed_unit_price,
    iff(activity.product_id is not null and activity.product_id = tariffs.product_id, 1, 0) as product_match_priority,
    iff(activity.service_id = tariffs.service_id, 1, 0) as service_match_priority,
    iff(tariffs.active_flag, 1, 0) as active_priority,
    iff(cast(activity.activity_datetime as date) between tariffs.valid_from and coalesce(tariffs.valid_to, to_date('9999-12-31')), 1, 0) as effective_priority,
    row_number() over (
        partition by activity.billable_activity_id
        order by product_match_priority desc, service_match_priority desc, effective_priority desc, active_priority desc, tariffs.version desc, tariffs.tariff_id asc
    ) as tariff_candidate_rank,
    count(*) over (partition by activity.billable_activity_id) as tariff_candidate_count
from activity
left join tariffs
    on activity.service_id = tariffs.service_id
    or (activity.product_id is not null and activity.product_id = tariffs.product_id)
left join claims
    on activity.billable_activity_id = claims.billable_activity_id
