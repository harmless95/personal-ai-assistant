from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from uuid import UUID

from app.api.daily_checkin.models.daily import QuestionCategory
from app.db import DailyQuestion
from app.tasks.components.models.day_summary import DaySummaryBuildResult


class DaySummaryClient(ABC):
    @abstractmethod
    async def build(
        self,
        *,
        checkin_id: UUID,
        questions: Sequence[DailyQuestion],
        answers_by_category: Mapping[QuestionCategory, str],
    ) -> DaySummaryBuildResult:
        pass
