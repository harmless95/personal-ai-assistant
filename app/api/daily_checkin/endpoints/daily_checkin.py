from fastapi import APIRouter

from app.api.daily_checkin.models.daily import (
    AnswerCheckinRequest,
    AnswerCheckinResponse,
    AskCheckinRequest,
    AskCheckinResponse,
)
from app.api.daily_checkin.services.service_daily import DailyCheckinService

router = APIRouter(prefix="/daily/checkin", tags=["daily-checkin"])


@router.post("/ask/", response_model=AskCheckinResponse)
async def check_state_client(client_data: AskCheckinRequest) -> AskCheckinResponse:
    service = DailyCheckinService()
    response = service.question_handler(client_data=client_data)
    return await response


@router.post("/answer/", response_model=AnswerCheckinResponse)
async def response_client(question_data: AnswerCheckinRequest) -> AnswerCheckinResponse:
    service = DailyCheckinService()
    response = service.answer_handler(question_data=question_data)
    return await response
