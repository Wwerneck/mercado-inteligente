select
    category_id,
    snapshot_date_key,
    domain_count,
    total_items_in_this_category,
    children_categories_count,
    category_depth,
    catalog_coverage_score
from {{ source('analytics', 'fact_category_snapshot') }}

