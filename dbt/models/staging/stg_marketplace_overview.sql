select
    snapshot_date_key,
    total_categories,
    total_domains,
    total_items_in_categories,
    avg_children_categories,
    latest_ingestion_at
from {{ source('analytics', 'fact_marketplace_overview') }}

