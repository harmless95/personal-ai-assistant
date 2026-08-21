from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from app.api.daily_checkin.data.daily_checkin_repository import DailyCheckinRepository
from app.db.session import session_getter
from app.tasks.components.clients.day_summary import DaySummaryClient, OpenAIDaySummaryClient
from app.tasks.services.day_summary_processor import DaySummaryProcessor

SessionDep = Annotated[AsyncSession, TaskiqDepends(session_getter)]


def get_repository(session: SessionDep) -> DailyCheckinRepository:
    return DailyCheckinRepository(session=session)


DailyCheckinRepositoryDep = Annotated[DailyCheckinRepository, TaskiqDepends(get_repository)]


def get_summary_client() -> DaySummaryClient:
    return OpenAIDaySummaryClient()


DaySummaryClientDep = Annotated[DaySummaryClient, TaskiqDepends(get_summary_client)]


def get_day_summary_processor(
    repository: DailyCheckinRepositoryDep,
    summary_client: DaySummaryClientDep,
) -> DaySummaryProcessor:
    return DaySummaryProcessor(repository=repository, summary_client=summary_client)


DaySummaryProcessorDep = Annotated[DaySummaryProcessor, TaskiqDepends(get_day_summary_processor)]
