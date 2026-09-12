from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ai.semantic_layer import Intent, classify_question
from src.api.repository import AnalyticsRepository


@dataclass(frozen=True)
class AssistantResponse:
    question: str
    intent: str
    answer: str
    sources: list[str]
    data: dict[str, Any]


class MarketplaceAssistant:
    def __init__(self, repository: AnalyticsRepository) -> None:
        self.repository = repository

    def answer(self, question: str) -> AssistantResponse:
        semantic_query = classify_question(question)
        if semantic_query.intent == Intent.TOP_OPPORTUNITIES:
            return self._top_opportunities(question)
        if semantic_query.intent == Intent.ANOMALIES:
            return self._anomalies(question)
        if semantic_query.intent == Intent.CATEGORY_VARIATION:
            return self._category_variation(question)
        if semantic_query.intent == Intent.MARKETPLACE_OVERVIEW:
            return self._overview(question)
        if semantic_query.intent == Intent.ADVANCED_ML_STATUS:
            return self._advanced_ml_status(question)
        if semantic_query.intent == Intent.SELLER_SUMMARY:
            return self._seller_summary(question)
        if semantic_query.intent == Intent.SELLER_TOP_CATEGORIES:
            return self._seller_top_categories(question)
        if semantic_query.intent == Intent.SELLER_STOCK:
            return self._seller_stock(question)
        if semantic_query.intent == Intent.SELLER_SALES:
            return self._seller_sales(question)
        if semantic_query.intent == Intent.SELLER_PAUSED_ITEMS:
            return self._seller_items_by_status(question, Intent.SELLER_PAUSED_ITEMS, "paused")
        if semantic_query.intent == Intent.SELLER_ZERO_SALES_ITEMS:
            return self._seller_zero_sales_items(question)
        if semantic_query.intent == Intent.SELLER_TOP_STOCK_ITEMS:
            return self._seller_top_items(question, Intent.SELLER_TOP_STOCK_ITEMS, "available_quantity")
        if semantic_query.intent == Intent.SELLER_EXPENSIVE_ITEMS:
            return self._seller_top_items(question, Intent.SELLER_EXPENSIVE_ITEMS, "price")
        if semantic_query.intent == Intent.SELLER_ACTIVE_ITEMS:
            return self._seller_items_by_status(question, Intent.SELLER_ACTIVE_ITEMS, "active")
        return AssistantResponse(
            question=question,
            intent=Intent.UNKNOWN.value,
            answer=(
                "Ainda nao tenho uma consulta segura para responder essa pergunta. "
                "Posso responder sobre oportunidades, anomalias, overview, variacao disponivel "
                "status de clustering/forecasting e metricas do seller autenticado."
            ),
            sources=[],
            data={},
        )

    def _top_opportunities(self, question: str) -> AssistantResponse:
        items, total = self.repository.ml_scores(limit=5, offset=0)
        if not items:
            answer = "Nao ha scores de oportunidade gerados no momento."
        else:
            leader = items[0]
            answer = (
                f"A melhor oportunidade atual e {leader['category_name']} "
                f"com score {leader['opportunity_score']}. "
                f"Foram avaliadas {total} categorias com base nos dados Gold e nas features de ML."
            )
        return AssistantResponse(
            question,
            Intent.TOP_OPPORTUNITIES.value,
            answer,
            ["data/gold/ml_category_scores.parquet"],
            {"items": items, "total": total},
        )

    def _anomalies(self, question: str) -> AssistantResponse:
        anomalies = self.repository.anomalies()
        if not anomalies:
            answer = "Nao ha anomalias marcadas no dataset atual."
        else:
            answer = f"Foram encontradas {len(anomalies)} anomalias no resultado de ML atual."
        return AssistantResponse(
            question,
            Intent.ANOMALIES.value,
            answer,
            ["data/gold/ml_category_scores.parquet", "data/gold/ml_model_metadata.json"],
            {"anomalies": anomalies},
        )

    def _category_variation(self, question: str) -> AssistantResponse:
        metadata = self.repository.advanced_ml_metadata()
        reason = metadata["readiness"]["forecasting"]["reason"]
        answer = (
            "Ainda nao ha historico temporal suficiente para calcular variacoes ou previsoes "
            f"de forma robusta. {reason}"
        )
        return AssistantResponse(
            question,
            Intent.CATEGORY_VARIATION.value,
            answer,
            ["data/gold/ml_advanced_metadata.json"],
            {"forecasting_readiness": metadata["readiness"]["forecasting"]},
        )

    def _overview(self, question: str) -> AssistantResponse:
        overview = self.repository.marketplace_overview()
        row = overview[0] if overview else {}
        answer = (
            "O marketplace monitorado possui "
            f"{row.get('total_categories', 0)} categorias, "
            f"{row.get('total_domains', 0)} dominios e "
            f"{row.get('total_items_in_categories', 0)} itens nas categorias avaliadas."
        )
        return AssistantResponse(
            question,
            Intent.MARKETPLACE_OVERVIEW.value,
            answer,
            ["main_marts.mart_marketplace_overview"],
            {"overview": overview},
        )

    def _advanced_ml_status(self, question: str) -> AssistantResponse:
        metadata = self.repository.advanced_ml_metadata()
        clustering = metadata["readiness"]["clustering"]
        forecasting = metadata["readiness"]["forecasting"]
        answer = (
            f"Clustering pronto: {clustering['ready']}. {clustering['reason']} "
            f"Forecasting pronto: {forecasting['ready']}. {forecasting['reason']}"
        )
        return AssistantResponse(
            question,
            Intent.ADVANCED_ML_STATUS.value,
            answer,
            ["data/gold/ml_advanced_metadata.json"],
            metadata,
        )

    def _seller_summary(self, question: str) -> AssistantResponse:
        items, total = self.repository.seller_item_metrics(limit=100, offset=0)
        if not items:
            answer = (
                "Ainda nao ha metricas do seller autenticado. "
                "Execute a coleta OAuth e depois a fase Silver/Gold."
            )
        else:
            item_count = sum(int(item["item_count"]) for item in items)
            active_count = sum(int(item["active_item_count"]) for item in items)
            category_count = len({item["category_id"] for item in items if item.get("category_id")})
            stock_without_sales = sum(int(item.get("zero_sales_stock_count") or 0) for item in items)
            answer = (
                f"O seller autenticado possui {item_count} anuncios monitorados, "
                f"{active_count} ativos, distribuidos em {category_count} categorias. "
                f"Ha {stock_without_sales} agrupamentos com estoque e nenhuma venda registrada."
            )
        return self._seller_response(question, Intent.SELLER_SUMMARY, answer, items, total)

    def _seller_top_categories(self, question: str) -> AssistantResponse:
        items, total = self.repository.seller_item_metrics(limit=100, offset=0)
        if not items:
            answer = (
                "Ainda nao ha categorias do seller autenticado para analisar. "
                "Execute a coleta OAuth e depois a fase Silver/Gold."
            )
        else:
            leader = max(items, key=lambda item: int(item["item_count"]))
            answer = (
                f"A categoria com mais anuncios e {leader.get('category_id')} "
                f"com {leader['item_count']} anuncios no status {leader['status']}."
            )
        return self._seller_response(question, Intent.SELLER_TOP_CATEGORIES, answer, items, total)

    def _seller_stock(self, question: str) -> AssistantResponse:
        items, total = self.repository.seller_item_metrics(limit=100, offset=0)
        if not items:
            answer = (
                "Ainda nao ha dados de estoque do seller autenticado. "
                "Execute a coleta OAuth e depois a fase Silver/Gold."
            )
        else:
            total_stock = sum(int(item["total_available_quantity"]) for item in items)
            leader = max(items, key=lambda item: int(item["total_available_quantity"]))
            stock_without_sales = sum(int(item.get("zero_sales_stock_count") or 0) for item in items)
            answer = (
                f"O estoque total monitorado e {total_stock}. "
                f"A maior concentracao esta em {leader.get('category_id')} "
                f"com {leader['total_available_quantity']} unidades. "
                f"Ha {stock_without_sales} agrupamentos com estoque sem vendas registradas."
            )
        return self._seller_response(question, Intent.SELLER_STOCK, answer, items, total)

    def _seller_sales(self, question: str) -> AssistantResponse:
        items, total = self.repository.seller_item_metrics(limit=100, offset=0)
        if not items:
            answer = (
                "Ainda nao ha dados de vendas do seller autenticado. "
                "Execute a coleta OAuth e depois a fase Silver/Gold."
            )
        else:
            total_sold = sum(int(item["total_sold_quantity"]) for item in items)
            leader = max(items, key=lambda item: int(item["total_sold_quantity"]))
            avg_sell_through = sum(float(item.get("sell_through_rate") or 0) for item in items) / len(items)
            answer = (
                f"O total vendido monitorado e {total_sold}. "
                f"A categoria com maior volume vendido e {leader.get('category_id')} "
                f"com {leader['total_sold_quantity']} unidades. "
                f"O sell-through medio dos agrupamentos e {round(avg_sell_through, 2)}%."
            )
        return self._seller_response(question, Intent.SELLER_SALES, answer, items, total)

    def _seller_response(
        self,
        question: str,
        intent: Intent,
        answer: str,
        items: list[dict[str, Any]],
        total: int,
    ) -> AssistantResponse:
        return AssistantResponse(
            question,
            intent.value,
            answer,
            ["data/gold/seller_item_metrics.parquet"],
            {"items": items, "total": total},
        )

    def _seller_items_by_status(
        self,
        question: str,
        intent: Intent,
        status: str,
    ) -> AssistantResponse:
        items, total = self.repository.seller_items(limit=100, offset=0, status=status)
        selected = items[:5]
        if not selected:
            answer = f"Nao encontrei anuncios com status {status} nos dados autenticados atuais."
        else:
            answer = _format_item_list(f"Encontrei {total} anuncios com status {status}.", selected)
        return self._seller_item_response(question, intent, answer, selected, total)

    def _seller_zero_sales_items(self, question: str) -> AssistantResponse:
        items, _ = self.repository.seller_items(limit=100, offset=0)
        selected = [
            item
            for item in items
            if int(item.get("sold_quantity") or 0) == 0
            and int(item.get("available_quantity") or 0) > 0
        ][:5]
        if not selected:
            answer = "Nao encontrei anuncios com estoque e zero venda registrada nos dados atuais."
        else:
            answer = _format_item_list(
                f"Encontrei {len(selected)} anuncios com estoque e zero venda registrada no top analisado.",
                selected,
            )
        return self._seller_item_response(
            question,
            Intent.SELLER_ZERO_SALES_ITEMS,
            answer,
            selected,
            len(selected),
        )

    def _seller_top_items(self, question: str, intent: Intent, metric: str) -> AssistantResponse:
        items, total = self.repository.seller_items(limit=100, offset=0)
        selected = sorted(items, key=lambda item: float(item.get(metric) or 0), reverse=True)[:5]
        if not selected:
            answer = "Ainda nao ha anuncios autenticados para listar."
        else:
            answer = _format_item_list(f"Top {len(selected)} anuncios por {metric}.", selected)
        return self._seller_item_response(question, intent, answer, selected, total)

    def _seller_item_response(
        self,
        question: str,
        intent: Intent,
        answer: str,
        items: list[dict[str, Any]],
        total: int,
    ) -> AssistantResponse:
        return AssistantResponse(
            question,
            intent.value,
            answer,
            ["main_marts.mart_seller_items"],
            {"items": items, "total": total},
        )


def _format_item_list(prefix: str, items: list[dict[str, Any]]) -> str:
    parts = [prefix]
    for item in items:
        title = item.get("title") or item.get("item_id")
        price = item.get("price")
        stock = item.get("available_quantity")
        sold = item.get("sold_quantity")
        status = item.get("status")
        parts.append(f"{title}: preco {price}, estoque {stock}, vendidos {sold}, status {status}.")
    return " ".join(parts)


def build_assistant(duckdb_path: Path, data_dir: Path) -> MarketplaceAssistant:
    return MarketplaceAssistant(AnalyticsRepository(duckdb_path, data_dir))
