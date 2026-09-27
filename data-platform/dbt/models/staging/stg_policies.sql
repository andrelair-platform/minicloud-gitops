-- Cleaned/typed view of raw policies. One row per policy.
with src as (
    select * from {{ source('policy_raw', 'policies') }}
)
select
    id                                   as policy_id,
    policy_number,
    holder_name,
    product_code,
    status,
    (status = 'active')                  as is_active,
    effective_date,
    expiry_date,
    extract(year from effective_date)::int  as inception_year,
    created_at,
    updated_at
from src
