-- Consultas locais em DuckDB

select *
from analytics.fact_marketplace_overview;

select
    c.category_name,
    f.total_items_in_this_category,
    f.catalog_coverage_score
from analytics.fact_category_snapshot f
join analytics.dim_category c using (category_id)
order by f.catalog_coverage_score desc;

