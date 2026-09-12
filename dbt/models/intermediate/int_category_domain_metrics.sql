select
    c.category_id,
    c.category_name,
    c.path_from_root,
    count(distinct d.domain_category_id) as discovered_domain_count
from {{ ref('stg_categories') }} c
left join {{ ref('stg_domains') }} d
    on c.category_id = d.category_id
group by
    c.category_id,
    c.category_name,
    c.path_from_root
