from fastapi import APIRouter

from app.api.daily_checkin.deps import DailyCheckinServiceDep
from app.api.daily_checkin.models.daily import (
    AnswerCheckinRequest,
    AnswerCheckinResponse,
    AskCheckinRequest,
    AskCheckinResponse,
)

router = APIRouter(prefix="/daily/checkin", tags=["daily-checkin"])


@router.post("/ask/", response_model=AskCheckinResponse)
async def ask_daily_checkin(
    client_data: AskCheckinRequest,
    service: DailyCheckinServiceDep,
) -> AskCheckinResponse:
    return await service.question_handler(client_data=client_data)


@router.post("/answer/", response_model=AnswerCheckinResponse)
async def answer_daily_checkin(
    question_data: AnswerCheckinRequest,
    service: DailyCheckinServiceDep,
) -> AnswerCheckinResponse:
    return await service.answer_handler(question_data=question_data)
