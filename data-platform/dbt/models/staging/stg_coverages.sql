-- Cleaned coverages. insured_amount / deductible are BIGINT minor units (assumed cents).
with src as (
    select * from {{ source('policy_raw', 'coverages') }}
)
select
    id                                   as coverage_id,
    policy_id,
    type                                 as coverage_type,
    insured_amount                       as insured_amount_minor,
    round(insured_amount / 100.0, 2)     as insured_amount_eur,
    deductible                           as deductible_minor
from src
