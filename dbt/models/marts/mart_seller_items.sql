select
    item_id,
    title,
    seller_id,
    category_id,
    status,
    condition,
    listing_type_id,
    permalink,
    price,
    available_quantity,
    sold_quantity,
    snapshot_date_key,
    snapshot_date
from {{ ref('stg_item_details') }}
