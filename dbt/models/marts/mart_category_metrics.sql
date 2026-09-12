select
    category_id,
    category_name,
    snapshot_date_key,
    snapshot_date,
    domain_count,
    discovered_domain_count,
    total_items_in_this_category,
    children_categories_count,
    category_depth,
    catalog_coverage_score,
    case
        when catalog_coverage_score >= 90 then 'high_coverage'
        when catalog_coverage_score >= 50 then 'medium_coverage'
        else 'low_coverage'
    end as coverage_band
from {{ ref('int_category_snapshot_enriched') }}

