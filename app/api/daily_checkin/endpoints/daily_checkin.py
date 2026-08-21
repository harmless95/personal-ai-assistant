from uuid import UUID

from fastapi import APIRouter, Query

from app.api.daily_checkin.deps import DailyCheckinServiceDep
from app.api.daily_checkin.models.daily import (
    AnswerCheckinRequest,
    AnswerCheckinResponse,
    ArtifactResponse,
    AskCheckinRequest,
    AskCheckinResponse,
    HistoryResponse,
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


@router.get("/history/", response_model=HistoryResponse)
async def get_checkin_history(
    user_id: UUID,
    service: DailyCheckinServiceDep,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> HistoryResponse:
    return await service.history_handler(user_id=user_id, limit=limit, offset=offset)


@router.get("/{checkin_id}/artifact/", response_model=ArtifactResponse)
async def get_checkin_artifact(
    checkin_id: UUID,
    user_id: UUID,
    service: DailyCheckinServiceDep,
) -> ArtifactResponse:
    return await service.artifact_handler(checkin_id=checkin_id, user_id=user_id)
