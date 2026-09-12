from typing import Annotated

from fastapi import APIRouter, Depends

from src.ai.assistant import MarketplaceAssistant
from src.api.dependencies import get_repository
from src.api.repository import AnalyticsRepository
from src.api.schemas import AssistantAnswer, AssistantQuestion

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/ask", response_model=AssistantAnswer)
def ask_assistant(
    payload: AssistantQuestion,
    repository: Annotated[AnalyticsRepository, Depends(get_repository)],
) -> dict:
    response = MarketplaceAssistant(repository).answer(payload.question)
    return response.__dict__
