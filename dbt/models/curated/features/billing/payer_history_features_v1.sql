{{ config(materialized='table', tags=['milestone_12', 'feature_store', 'billing_feature']) }}

with payments as (

    select * from {{ ref('fct_payment') }}

), payers as (

    select * from {{ ref('dim_payer') }}

), observations as (

    select
        payer_key,
        payment_datetime as observation_timestamp
    from payments

), feature_rows as (

    select
        observations.payer_key as entity_key,
        observations.observation_timestamp,
        observations.observation_timestamp as event_timestamp,
        observations.observation_timestamp as availability_timestamp,
        count(payments.payment_key) as prior_payment_count_90d,
        coalesce(sum(payments.amount), 0)::number(18,2) as prior_payment_amount_90d
    from observations
    left join payments
        on observations.payer_key = payments.payer_key
        and payments.payment_datetime < observations.observation_timestamp
        and payments.payment_datetime >= dateadd(day, -90, observations.observation_timestamp)
    group by observations.payer_key, observations.observation_timestamp

)

select
    {{ generate_healthcare_surrogate_key([
        "'payer_history_features_v1'",
        'feature_rows.entity_key',
        'feature_rows.observation_timestamp'
    ]) }} as feature_row_key,
    feature_rows.entity_key,
    feature_rows.observation_timestamp,
    feature_rows.event_timestamp,
    feature_rows.availability_timestamp,
    feature_rows.prior_payment_count_90d,
    feature_rows.prior_payment_amount_90d,
    coalesce(payers.payer_type, 'UNKNOWN') as payer_type,
    'payer_history_features_v1' as feature_view_id,
    '1.0.0' as feature_view_version,
    iff(feature_rows.prior_payment_count_90d = 0, 'NOT_APPLICABLE', 'FRESH') as freshness_status,
    iff(feature_rows.prior_payment_count_90d = 0, 'NO_PRIOR_PAYMENTS', 'AVAILABLE')
        as missing_feature_status,
    'fct_payment,dim_payer' as source_lineage,
    true as synthetic_flag,
    current_timestamp() as dbt_updated_at
from feature_rows
left join payers
    on feature_rows.entity_key = payers.payer_key
