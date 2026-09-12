select
    date_key,
    date,
    year,
    month,
    day
from {{ source('analytics', 'dim_date') }}

