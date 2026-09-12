select
    o.snapshot_date_key,
    d.date as snapshot_date,
    o.total_categories,
    o.total_domains,
    o.total_items_in_categories,
    o.avg_children_categories,
    o.latest_ingestion_at
from {{ ref('stg_marketplace_overview') }} o
left join {{ ref('stg_dates') }} d
    on o.snapshot_date_key = d.date_key

