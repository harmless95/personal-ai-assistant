from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.daily_checkin.clients.day_summary import DaySummaryClient, OpenAIDaySummaryClient
from app.api.daily_checkin.data.daily_checkin_repository import DailyCheckinRepository
from app.api.daily_checkin.services.service_daily import DailyCheckinService
from app.db.session import session_getter

SessionDep = Annotated[AsyncSession, Depends(session_getter)]


def get_repository(session: SessionDep) -> DailyCheckinRepository:
    return DailyCheckinRepository(session=session)


DailyCheckinRepositoryDep = Annotated[DailyCheckinRepository, Depends(get_repository)]


def get_summary_client() -> DaySummaryClient:
    return OpenAIDaySummaryClient()


DaySummaryClientDep = Annotated[DaySummaryClient, Depends(get_summary_client)]


def get_service(
    repository: DailyCheckinRepositoryDep,
    summary_client: DaySummaryClientDep,
) -> DailyCheckinService:
    return DailyCheckinService(repository=repository, summary_client=summary_client)


DailyCheckinServiceDep = Annotated[DailyCheckinService, Depends(get_service)]
