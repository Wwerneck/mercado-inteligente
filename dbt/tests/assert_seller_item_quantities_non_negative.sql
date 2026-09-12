select *
from {{ ref('stg_item_details') }}
where available_quantity < 0
   or sold_quantity < 0
