from dataclasses import dataclass
from enum import StrEnum


class Intent(StrEnum):
    TOP_OPPORTUNITIES = "top_opportunities"
    ANOMALIES = "anomalies"
    CATEGORY_VARIATION = "category_variation"
    MARKETPLACE_OVERVIEW = "marketplace_overview"
    ADVANCED_ML_STATUS = "advanced_ml_status"
    SELLER_SUMMARY = "seller_summary"
    SELLER_TOP_CATEGORIES = "seller_top_categories"
    SELLER_STOCK = "seller_stock"
    SELLER_SALES = "seller_sales"
    SELLER_PAUSED_ITEMS = "seller_paused_items"
    SELLER_ZERO_SALES_ITEMS = "seller_zero_sales_items"
    SELLER_TOP_STOCK_ITEMS = "seller_top_stock_items"
    SELLER_EXPENSIVE_ITEMS = "seller_expensive_items"
    SELLER_ACTIVE_ITEMS = "seller_active_items"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SemanticQuery:
    intent: Intent
    confidence: float


def classify_question(question: str) -> SemanticQuery:
    normalized = question.lower()
    seller_terms = ["seller", "vendedor", "anuncio", "anuncios", "produto", "produtos", "estoque", "vendidos"]
    if any(term in normalized for term in seller_terms):
        item_level_terms = ["liste", "lista", "quais anuncios", "quais produtos", "anuncios que", "produtos que"]
        is_item_level = any(term in normalized for term in item_level_terms)
        if is_item_level and any(term in normalized for term in ["pausado", "pausados", "paused"]):
            return SemanticQuery(Intent.SELLER_PAUSED_ITEMS, 0.9)
        if is_item_level and any(
            term in normalized
            for term in ["sem venda", "sem vendas", "nao venderam", "não venderam", "zero venda"]
        ):
            return SemanticQuery(Intent.SELLER_ZERO_SALES_ITEMS, 0.9)
        if is_item_level and any(term in normalized for term in ["estoque", "disponivel", "available"]):
            return SemanticQuery(Intent.SELLER_TOP_STOCK_ITEMS, 0.9)
        if is_item_level and any(term in normalized for term in ["caro", "caros", "maior preco", "preco maior"]):
            return SemanticQuery(Intent.SELLER_EXPENSIVE_ITEMS, 0.9)
        if is_item_level and any(term in normalized for term in ["ativo", "ativos", "active"]):
            return SemanticQuery(Intent.SELLER_ACTIVE_ITEMS, 0.9)
        if any(
            term in normalized
            for term in ["vendi", "venda", "vendas", "vender", "vendeu", "venderam", "sales"]
        ):
            return SemanticQuery(Intent.SELLER_SALES, 0.88)
        if any(term in normalized for term in ["estoque", "disponivel", "available"]):
            return SemanticQuery(Intent.SELLER_STOCK, 0.88)
        if any(term in normalized for term in ["categoria", "categorias", "maior", "mais"]):
            return SemanticQuery(Intent.SELLER_TOP_CATEGORIES, 0.86)
        return SemanticQuery(Intent.SELLER_SUMMARY, 0.82)
    if any(term in normalized for term in ["oportunidade", "opportunity", "score", "melhores"]):
        return SemanticQuery(Intent.TOP_OPPORTUNITIES, 0.9)
    if any(term in normalized for term in ["anomalia", "anormal", "outlier"]):
        return SemanticQuery(Intent.ANOMALIES, 0.9)
    if any(term in normalized for term in ["variação", "variacao", "mudança", "mudanca", "preço", "preco"]):
        return SemanticQuery(Intent.CATEGORY_VARIATION, 0.75)
    if any(term in normalized for term in ["overview", "resumo", "geral", "kpi", "indicadores"]):
        return SemanticQuery(Intent.MARKETPLACE_OVERVIEW, 0.85)
    if any(term in normalized for term in ["forecast", "previs", "cluster", "clustering"]):
        return SemanticQuery(Intent.ADVANCED_ML_STATUS, 0.85)
    return SemanticQuery(Intent.UNKNOWN, 0.0)
