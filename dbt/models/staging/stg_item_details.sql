select
    item.item_id,
    item.title,
    snapshot.price,
    snapshot.available_quantity,
    snapshot.sold_quantity,
    coalesce(snapshot.status, 'unknown') as status,
    item.condition,
    item.category_id,
    item.listing_type_id,
    item.permalink,
    item.seller_id,
    snapshot.snapshot_date_key,
    date_dim.date as snapshot_date
from {{ source('analytics', 'fact_seller_item_snapshot') }} as snapshot
left join {{ source('analytics', 'dim_item') }} as item
    on snapshot.item_id = item.item_id
left join {{ source('analytics', 'dim_date') }} as date_dim
    on snapshot.snapshot_date_key = date_dim.date_key
