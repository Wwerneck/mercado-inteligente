select
    domain_category_id,
    domain_id,
    domain_name,
    category_id,
    category_name,
    search_query
from {{ source('analytics', 'dim_domain') }}
