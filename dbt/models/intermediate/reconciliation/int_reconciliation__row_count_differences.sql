{{ config(materialized='ephemeral', tags=['milestone_6', 'core', 'reconciliation']) }}

select
    'PATIENT' as entity_name,
    (select count(*) from {{ ref('stg_clinical__patients') }}) as staging_row_count,
    (select count(*) from {{ ref('core_patient') }}) as core_row_count,
    'ONE_TO_ONE_EXPECTED' as reconciliation_rule
union all
select
    'ORGANISATION',
    (select count(*) from {{ ref('stg_operational__organisations') }}),
    (select count(*) from {{ ref('core_organisation') }}),
    'ONE_TO_ONE_EXPECTED'
union all
select
    'ENCOUNTER',
    (select count(*) from {{ ref('stg_clinical__encounters') }}),
    (select count(*) from {{ ref('core_encounter') }}),
    'ONE_TO_ONE_EXPECTED'
