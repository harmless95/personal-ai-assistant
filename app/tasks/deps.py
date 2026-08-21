from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from app.api.daily_checkin.data.daily_checkin_repository import DailyCheckinRepository
from app.config import settings
from app.db.session import session_getter
from app.tasks.components.clients.base import DaySummaryClient
from app.tasks.components.clients.openai import OpenAIDaySummaryClient
from app.tasks.components.clients.template import TemplateDaySummaryClient
from app.tasks.components.providers import DaySummaryProvider
from app.tasks.services.day_summary_processor import DaySummaryProcessor

SessionDep = Annotated[AsyncSession, TaskiqDepends(session_getter)]


def get_repository(session: SessionDep) -> DailyCheckinRepository:
    return DailyCheckinRepository(session=session)


DailyCheckinRepositoryDep = Annotated[DailyCheckinRepository, TaskiqDepends(get_repository)]


def get_summary_client(provider: str | None = None) -> DaySummaryClient:
    raw_provider = provider or settings.day_summary.provider
    try:
        resolved_provider = DaySummaryProvider(raw_provider)
    except ValueError as e:
        raise ValueError(f"unsupported day summary provider: {raw_provider}") from e

    if resolved_provider is DaySummaryProvider.OPENAI:
        return OpenAIDaySummaryClient()
    if resolved_provider is DaySummaryProvider.TEMPLATE:
        return TemplateDaySummaryClient()

    raise ValueError(f"unsupported day summary provider: {resolved_provider}")


DaySummaryClientDep = Annotated[DaySummaryClient, TaskiqDepends(get_summary_client)]


def get_day_summary_processor(
    repository: DailyCheckinRepositoryDep,
    summary_client: DaySummaryClientDep,
) -> DaySummaryProcessor:
    return DaySummaryProcessor(repository=repository, summary_client=summary_client)


DaySummaryProcessorDep = Annotated[DaySummaryProcessor, TaskiqDepends(get_day_summary_processor)]
