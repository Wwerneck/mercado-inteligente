create schema if not exists analytics;

create table if not exists analytics.dim_category (
    category_id varchar primary key,
    category_name varchar not null,
    path_from_root varchar,
    attribute_types varchar,
    settings_adult_content boolean
);

create table if not exists analytics.dim_domain (
    domain_category_id varchar primary key,
    domain_id varchar not null,
    domain_name varchar not null,
    category_id varchar not null references analytics.dim_category(category_id),
    category_name varchar,
    search_query varchar
);

create table if not exists analytics.dim_date (
    date_key bigint primary key,
    date varchar not null,
    year bigint not null,
    month bigint not null,
    day bigint not null
);

create table if not exists analytics.dim_seller (
    seller_id varchar primary key
);

create table if not exists analytics.dim_item (
    item_id varchar primary key,
    title varchar,
    category_id varchar references analytics.dim_category(category_id),
    seller_id varchar references analytics.dim_seller(seller_id),
    condition varchar,
    listing_type_id varchar,
    permalink varchar
);

create table if not exists analytics.fact_category_snapshot (
    category_id varchar not null references analytics.dim_category(category_id),
    snapshot_date_key bigint not null references analytics.dim_date(date_key),
    domain_count bigint not null,
    total_items_in_this_category bigint,
    children_categories_count bigint not null,
    category_depth bigint not null,
    catalog_coverage_score double precision not null,
    primary key (category_id, snapshot_date_key)
);

create table if not exists analytics.fact_marketplace_overview (
    snapshot_date_key bigint primary key references analytics.dim_date(date_key),
    total_categories bigint not null,
    total_domains bigint not null,
    total_items_in_categories bigint not null,
    avg_children_categories double precision not null,
    latest_ingestion_at timestamp
);

create table if not exists analytics.fact_seller_item_snapshot (
    item_id varchar not null references analytics.dim_item(item_id),
    snapshot_date_key bigint not null references analytics.dim_date(date_key),
    price double precision,
    available_quantity bigint,
    sold_quantity bigint,
    status varchar,
    primary key (item_id, snapshot_date_key)
);
