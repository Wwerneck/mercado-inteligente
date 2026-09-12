select
    category_id,
    category_name,
    path_from_root,
    attribute_types,
    settings_adult_content
from {{ source('analytics', 'dim_category') }}

