from src.ai.assistant import MarketplaceAssistant


class SellerRepositoryStub:
    def __init__(self, metrics=None, items=None):
        self.metrics = metrics or []
        self.items = items or []

    def seller_item_metrics(self, limit: int, offset: int):
        return self.metrics[offset : offset + limit], len(self.metrics)

    def seller_items(
        self,
        limit: int,
        offset: int,
        seller_id: str | None = None,
        category_id: str | None = None,
        status: str | None = None,
    ):
        items = self.items
        if seller_id:
            items = [item for item in items if item.get("seller_id") == seller_id]
        if category_id:
            items = [item for item in items if item.get("category_id") == category_id]
        if status:
            items = [item for item in items if item.get("status") == status]
        return items[offset : offset + limit], len(items)


def test_assistant_answers_seller_summary_from_gold_metrics():
    assistant = MarketplaceAssistant(
        SellerRepositoryStub(
            metrics=[
                {
                    "seller_id": "123",
                    "category_id": "MLB1",
                    "status": "active",
                    "item_count": 2,
                    "active_item_count": 2,
                    "total_available_quantity": 5,
                    "total_sold_quantity": 3,
                    "sell_through_rate": 37.5,
                    "zero_sales_stock_count": 0,
                },
                {
                    "seller_id": "123",
                    "category_id": "MLB2",
                    "status": "paused",
                    "item_count": 1,
                    "active_item_count": 0,
                    "total_available_quantity": 1,
                    "total_sold_quantity": 0,
                    "sell_through_rate": 0,
                    "zero_sales_stock_count": 1,
                },
            ]
        )
    )

    response = assistant.answer("Quantos anuncios ativos o seller possui?")

    assert response.intent == "seller_summary"
    assert "3 anuncios" in response.answer
    assert "2 ativos" in response.answer
    assert "estoque" in response.answer
    assert response.sources == ["data/gold/seller_item_metrics.parquet"]


def test_assistant_does_not_invent_seller_metrics_when_empty():
    assistant = MarketplaceAssistant(SellerRepositoryStub())

    response = assistant.answer("Quais categorias do seller venderam mais?")

    assert response.intent == "seller_sales"
    assert "Ainda nao ha dados" in response.answer
    assert response.data["total"] == 0


def test_assistant_lists_paused_seller_items():
    assistant = MarketplaceAssistant(
        SellerRepositoryStub(
            items=[
                {
                    "item_id": "MLB1",
                    "title": "Notebook",
                    "status": "paused",
                    "price": 100,
                    "available_quantity": 5,
                    "sold_quantity": 0,
                }
            ]
        )
    )

    response = assistant.answer("Quais anuncios estao pausados?")

    assert response.intent == "seller_paused_items"
    assert "Notebook" in response.answer
    assert response.sources == ["main_marts.mart_seller_items"]


def test_assistant_lists_expensive_seller_items_sorted():
    assistant = MarketplaceAssistant(
        SellerRepositoryStub(
            items=[
                {"item_id": "MLB1", "title": "Barato", "status": "active", "price": 10},
                {"item_id": "MLB2", "title": "Caro", "status": "active", "price": 100},
            ]
        )
    )

    response = assistant.answer("Quais anuncios sao mais caros?")

    assert response.intent == "seller_expensive_items"
    assert response.data["items"][0]["title"] == "Caro"
