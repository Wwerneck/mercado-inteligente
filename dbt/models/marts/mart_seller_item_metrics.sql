select
    seller_id,
    category_id,
    coalesce(status, 'unknown') as status,
    count(distinct item_id) as item_count,
    sum(case when status = 'active' then 1 else 0 end) as active_item_count,
    round(avg(price), 2) as avg_price,
    min(price) as min_price,
    max(price) as max_price,
    sum(coalesce(available_quantity, 0)) as total_available_quantity,
    sum(coalesce(sold_quantity, 0)) as total_sold_quantity,
    round(
        case
            when sum(coalesce(available_quantity, 0)) + sum(coalesce(sold_quantity, 0)) > 0
                then (
                    sum(coalesce(sold_quantity, 0))
                    / (sum(coalesce(available_quantity, 0)) + sum(coalesce(sold_quantity, 0)))
                ) * 100
            else 0
        end,
        2
    ) as sell_through_rate,
    max(price) - min(price) as price_spread,
    sum(case when status = 'paused' then 1 else 0 end) as paused_item_count,
    sum(
        case
            when coalesce(available_quantity, 0) > 0 and coalesce(sold_quantity, 0) = 0 then 1
            else 0
        end
    ) as zero_sales_stock_count,
    max(snapshot_date) as latest_snapshot_date
from {{ ref('stg_item_details') }}
group by
    seller_id,
    category_id,
    coalesce(status, 'unknown')
