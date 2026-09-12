from src.ai.semantic_layer import Intent, classify_question


def test_classify_question_detects_opportunities():
    result = classify_question("Quais categorias possuem maior Opportunity Score?")

    assert result.intent == Intent.TOP_OPPORTUNITIES


def test_classify_question_detects_unknown():
    result = classify_question("Qual e a cor do logo?")

    assert result.intent == Intent.UNKNOWN


def test_classify_question_detects_seller_stock_before_price_variation():
    result = classify_question("Quais categorias do seller tem mais estoque?")

    assert result.intent == Intent.SELLER_STOCK


def test_classify_question_detects_seller_sales():
    result = classify_question("Quais produtos vendidos tiveram maior volume?")

    assert result.intent == Intent.SELLER_SALES


def test_classify_question_detects_seller_item_level_intents():
    assert classify_question("Quais anuncios estao pausados?").intent == Intent.SELLER_PAUSED_ITEMS
    assert classify_question("Quais anuncios sao mais caros?").intent == Intent.SELLER_EXPENSIVE_ITEMS
    assert classify_question("Liste meus anuncios ativos.").intent == Intent.SELLER_ACTIVE_ITEMS
