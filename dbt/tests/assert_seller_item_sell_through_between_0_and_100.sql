select *
from {{ ref('mart_seller_item_metrics') }}
where sell_through_rate < 0
   or sell_through_rate > 100
