-- Foundation monitoring queries; results are live evidence only when actually executed.
-- noqa: disable=PRS
show warehouses like 'HEDP_DEV_%';
show resource monitors like 'HEDP_DEV_%';
show grants to role HEDP_DEV_PLATFORM_OWNER;

select
    warehouse_name,
    sum(credits_used) as credits_used
from snowflake.account_usage.warehouse_metering_history
where start_time >= dateadd(day, -7, current_timestamp())
    and warehouse_name like 'HEDP_DEV_%'
group by warehouse_name
order by warehouse_name;

select
    query_id,
    user_name,
    role_name,
    warehouse_name,
    execution_status,
    error_code,
    total_elapsed_time
from snowflake.account_usage.query_history
where start_time >= dateadd(day, -1, current_timestamp())
    and (warehouse_name like 'HEDP_DEV_%' or execution_status = 'FAIL')
order by start_time desc
limit 100;
