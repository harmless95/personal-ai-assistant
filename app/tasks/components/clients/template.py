from collections.abc import Mapping, Sequence
from uuid import UUID

from app.api.daily_checkin.models.daily import AnswerCheckinResponse, QuestionCategory
from app.api.daily_checkin.utils.summary import build_answer_response
from app.db import DailyQuestion
from app.tasks.components.clients.base import DaySummaryClient


class TemplateDaySummaryClient(DaySummaryClient):
    async def build(
        self,
        *,
        checkin_id: UUID,
        questions: Sequence[DailyQuestion],
        answers_by_category: Mapping[QuestionCategory, str],
    ) -> AnswerCheckinResponse:
        _ = questions
        return build_answer_response(
            checkin_id=checkin_id,
            answers_by_category=dict(answers_by_category),
        )
