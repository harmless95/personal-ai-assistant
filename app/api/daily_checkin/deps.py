from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.daily_checkin.data.daily_checkin_repository import DailyCheckinRepository
from app.api.daily_checkin.services.service_daily import DailyCheckinService
from app.db.session import session_getter

SessionDep = Annotated[AsyncSession, Depends(session_getter)]


def get_repository(session: SessionDep) -> DailyCheckinRepository:
    return DailyCheckinRepository(session=session)


DailyCheckinRepositoryDep = Annotated[DailyCheckinRepository, Depends(get_repository)]


def get_service(repository: DailyCheckinRepositoryDep) -> DailyCheckinService:
    return DailyCheckinService(repository=repository)


DailyCheckinServiceDep = Annotated[DailyCheckinService, Depends(get_service)]
