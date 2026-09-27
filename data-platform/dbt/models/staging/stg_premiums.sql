-- Cleaned premiums. amount is BIGINT minor units (assumed cents — CONFIRM with Policy domain);
-- exposed both as _minor and _eur. annualised = amount x cadence multiplier.
with src as (
    select * from {{ source('policy_raw', 'premiums') }}
)
select
    id                                   as premium_id,
    policy_id,
    amount                               as amount_minor,
    round(amount / 100.0, 2)             as amount_eur,
    frequency,
    case frequency
        when 'monthly'   then 12
        when 'quarterly' then 4
        when 'annual'    then 1
    end                                  as annual_multiplier,
    amount * case frequency
        when 'monthly'   then 12
        when 'quarterly' then 4
        when 'annual'    then 1
    end                                  as annualised_amount_minor,
    due_date,
    paid_at,
    (paid_at is not null)                as is_paid
from src
