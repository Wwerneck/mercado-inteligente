select
    s.category_id,
    c.category_name,
    s.snapshot_date_key,
    dt.date as snapshot_date,
    s.domain_count,
    d.discovered_domain_count,
    s.total_items_in_this_category,
    s.children_categories_count,
    s.category_depth,
    s.catalog_coverage_score
from {{ ref('stg_category_snapshots') }} s
left join {{ ref('stg_categories') }} c
    on s.category_id = c.category_id
left join {{ ref('stg_dates') }} dt
    on s.snapshot_date_key = dt.date_key
left join {{ ref('int_category_domain_metrics') }} d
    on s.category_id = d.category_id

