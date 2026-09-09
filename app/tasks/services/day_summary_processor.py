from collections.abc import Mapping
from uuid import UUID

import structlog

from app.api.daily_checkin.data.daily_checkin_repository import DailyCheckinRepository
from app.api.daily_checkin.models.daily import AnswerItem, ArtifactStatus, QuestionCategory
from app.api.daily_checkin.utils.checkin import attach_artifact, mark_artifact_failed
from app.api.daily_checkin.utils.summary import map_answers_by_category, structured_summary_from_response
from app.knowledge import KnowledgeGrpcClient, KnowledgeSearchError
from app.knowledge.models import KnowledgeChunkHit
from app.tasks.components.clients.base import DaySummaryClient
from app.tasks.services.knowledge_query import build_knowledge_query

logger = structlog.get_logger(__name__)


class DaySummaryProcessor:
    def __init__(
        self,
        repository: DailyCheckinRepository,
        summary_client: DaySummaryClient,
        knowledge_client: KnowledgeGrpcClient,
    ):
        self.repository = repository
        self.summary_client = summary_client
        self.knowledge_client = knowledge_client

    async def process_checkin(self, checkin_id: UUID) -> None:
        checkin = await self.repository.get_checkin_by_id(
            checkin_id=checkin_id,
            with_questions=True,
            with_answers=True,
            with_artifact=True,
        )
        if checkin is None:
            logger.warning("day_summary_checkin_not_found", checkin_id=str(checkin_id))
            return
        if checkin.artifact_status == ArtifactStatus.READY and checkin.artifact is not None:
            logger.info("day_summary_already_exists", checkin_id=str(checkin_id))
            return
        if not checkin.answers:
            logger.warning("day_summary_missing_answers", checkin_id=str(checkin_id))
            mark_artifact_failed(checkin)
            await self.repository.save_checkin(checkin=checkin)
            return

        answers = [
            AnswerItem(question_id=answer.question_id, answer_text=answer.answer_text) for answer in checkin.answers
        ]
        answers_by_category = map_answers_by_category(questions=checkin.questions, answers=answers)
        if not answers_by_category:
            logger.warning("day_summary_empty_category_map", checkin_id=str(checkin_id))
            mark_artifact_failed(checkin)
            await self.repository.save_checkin(checkin=checkin)
            return

        knowledge_chunks = await self._fetch_knowledge_chunks(
            checkin_id=checkin.id,
            answers_by_category=answers_by_category,
        )
        build_result = await self.summary_client.build(
            checkin_id=checkin.id,
            questions=checkin.questions,
            answers_by_category=answers_by_category,
            knowledge_chunks=knowledge_chunks,
        )
        attach_artifact(
            checkin,
            structured_summary=structured_summary_from_response(build_result.response),
            source=build_result.source,
        )
        await self.repository.save_checkin(checkin=checkin)
        logger.info(
            "day_summary_saved",
            checkin_id=str(checkin_id),
            source=build_result.source.value,
            categories=sorted(category.value for category in answers_by_category),
            knowledge_chunks=len(knowledge_chunks),
            **build_result.metrics.as_log_fields(),
        )

    async def _fetch_knowledge_chunks(
        self,
        *,
        checkin_id: UUID,
        answers_by_category: Mapping[QuestionCategory, str],
    ) -> list[KnowledgeChunkHit]:
        query = build_knowledge_query(answers_by_category)
        if not query:
            return []
        try:
            chunks = await self.knowledge_client.search(query)
        except KnowledgeSearchError:
            logger.warning(
                "day_summary_knowledge_search_failed",
                checkin_id=str(checkin_id),
                exc_info=True,
            )
            return []

        logger.info(
            "day_summary_knowledge_retrieved",
            checkin_id=str(checkin_id),
            chunks=len(chunks),
            query_preview=query[:120],
        )
        return chunks
