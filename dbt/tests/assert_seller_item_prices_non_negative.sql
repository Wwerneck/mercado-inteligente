select *
from {{ ref('stg_item_details') }}
where price < 0
