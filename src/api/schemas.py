from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class CategoryMetric(BaseModel):
    category_id: str
    category_name: str
    snapshot_date_key: int
    snapshot_date: str | None = None
    domain_count: int
    discovered_domain_count: int | None = None
    total_items_in_this_category: int | None = None
    children_categories_count: int
    category_depth: int
    catalog_coverage_score: float
    coverage_band: str | None = None


class MarketplaceOverview(BaseModel):
    snapshot_date_key: int
    snapshot_date: str | None = None
    total_categories: int
    total_domains: int
    total_items_in_categories: int
    avg_children_categories: float
    latest_ingestion_at: str | None = None


class SellerItemMetric(BaseModel):
    seller_id: str | None = None
    category_id: str | None = None
    status: str
    item_count: int
    active_item_count: int
    avg_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    total_available_quantity: int
    total_sold_quantity: int
    sell_through_rate: float | None = None
    price_spread: float | None = None
    paused_item_count: int | None = None
    zero_sales_stock_count: int | None = None
    latest_ingestion_at: str | None = None
    latest_snapshot_date: str | None = None


class SellerItem(BaseModel):
    item_id: str
    title: str | None = None
    seller_id: str | None = None
    category_id: str | None = None
    status: str
    condition: str | None = None
    listing_type_id: str | None = None
    permalink: str | None = None
    price: float | None = None
    available_quantity: int | None = None
    sold_quantity: int | None = None
    snapshot_date_key: int
    snapshot_date: str | None = None


class MLCategoryScore(BaseModel):
    category_id: str
    category_name: str
    anomaly_score: float
    is_anomaly: bool
    anomaly_type: str
    opportunity_score: float
    opportunity_rank: int


class PaginatedResponse(BaseModel):
    items: list[dict[str, Any]]
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
    total: int


class AssistantQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AssistantAnswer(BaseModel):
    question: str
    intent: str
    answer: str
    sources: list[str]
    data: dict[str, Any]


class PipelineRunSummary(BaseModel):
    run_id: str | None = None
    status: str | None = None
    query: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    task_count: int
    task_statuses: dict[str, str]
    manifest_path: str


class MeliAuthorizationResponse(BaseModel):
    authorization_url: str
    state: str
    code_verifier: str | None = None
    code_challenge_method: str | None = None


class MeliOAuthCallbackRequest(BaseModel):
    code: str = Field(min_length=1)
    state: str = Field(min_length=1)
    expected_state: str | None = Field(default=None, min_length=1)
    code_verifier: str | None = Field(default=None, min_length=1)


class MeliRefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class MeliTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    scope: str | None = None
    user_id: int | None = None
    refresh_token: str | None = None


class MeliTokenStatusResponse(BaseModel):
    configured: bool
    token_path: str
    token: dict[str, Any] | None = None
