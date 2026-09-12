select *
from {{ ref('mart_category_metrics') }}
where catalog_coverage_score < 0
   or catalog_coverage_score > 100

