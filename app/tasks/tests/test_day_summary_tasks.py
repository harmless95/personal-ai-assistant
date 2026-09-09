from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from app.api.daily_checkin.models.daily import ArtifactSource, ArtifactStatus, CheckinStatus, QuestionCategory
from app.db import DailyArtifact, DailyCheckin, DailyQuestion, QuestionAnswer
from app.knowledge import KnowledgeGrpcClient
from app.knowledge.client import KnowledgeSearchError
from app.knowledge.models import KnowledgeChunkHit
from app.tasks.components.clients.template import TemplateDaySummaryClient
from app.tasks.enqueue import enqueue_day_summary
from app.tasks.services.day_summary_processor import DaySummaryProcessor


def _disabled_knowledge_client() -> KnowledgeGrpcClient:
    return KnowledgeGrpcClient(target="localhost:50051", enabled=False)


def _sample_checkin() -> tuple[UUID, DailyCheckin]:
    checkin_id = uuid4()
    checkin = DailyCheckin(
        id=checkin_id,
        user_id=uuid4(),
        status=CheckinStatus.ANSWERED,
        stress_level=3,
        energy_level=3,
        plan_done=3,
        blocker_present=0,
        learning_done=3,
        questions=[
            DailyQuestion(question_id=uuid4(), category=QuestionCategory.RISK, text="Risk?", sort_order=1),
            DailyQuestion(question_id=uuid4(), category=QuestionCategory.FOCUS, text="Focus?", sort_order=2),
            DailyQuestion(question_id=uuid4(), category=QuestionCategory.ENERGY, text="Energy?", sort_order=3),
            DailyQuestion(question_id=uuid4(), category=QuestionCategory.LEARNING, text="Learning?", sort_order=4),
            DailyQuestion(question_id=uuid4(), category=QuestionCategory.ACTION, text="Action?", sort_order=5),
        ],
        answers=[],
        artifact=None,
    )
    checkin.answers = [
        QuestionAnswer(question_id=checkin.questions[0].question_id, answer_text="Meetings"),
        QuestionAnswer(question_id=checkin.questions[1].question_id, answer_text="Distractions"),
        QuestionAnswer(question_id=checkin.questions[2].question_id, answer_text="No breaks"),
        QuestionAnswer(question_id=checkin.questions[3].question_id, answer_text="Learned scoring"),
        QuestionAnswer(question_id=checkin.questions[4].question_id, answer_text="Ship"),
    ]
    return checkin_id, checkin


@pytest.mark.asyncio
async def test_enqueue_day_summary_success() -> None:
    with patch("app.tasks.enqueue.process_day_summary.kiq", new_callable=AsyncMock) as mock_kiq:
        assert await enqueue_day_summary("checkin-id") is True
        mock_kiq.assert_awaited_once_with("checkin-id")


@pytest.mark.asyncio
async def test_enqueue_day_summary_failure() -> None:
    with patch(
        "app.tasks.enqueue.process_day_summary.kiq",
        new_callable=AsyncMock,
        side_effect=RuntimeError("redis down"),
    ):
        assert await enqueue_day_summary("checkin-id") is False


@pytest.mark.asyncio
async def test_day_summary_processor_saves_artifact() -> None:
    checkin_id, checkin = _sample_checkin()
    repository: Any = Mock()
    repository.get_checkin_by_id = AsyncMock(return_value=checkin)
    repository.save_checkin = AsyncMock(return_value=checkin)
    processor = DaySummaryProcessor(
        repository=repository,
        summary_client=TemplateDaySummaryClient(),
        knowledge_client=_disabled_knowledge_client(),
    )

    await processor.process_checkin(checkin_id=checkin_id)

    assert checkin.artifact is not None
    assert checkin.artifact_status == ArtifactStatus.READY
    assert checkin.artifact.source == ArtifactSource.TEMPLATE
    assert "Meetings" in checkin.artifact.structured_summary_json["day_summary"]
    repository.save_checkin.assert_awaited_once()


@pytest.mark.asyncio
async def test_day_summary_processor_passes_knowledge_chunks() -> None:
    checkin_id, checkin = _sample_checkin()
    hit = KnowledgeChunkHit(
        chunk_id="1",
        source="tips.md",
        chunk_index=0,
        text="Take breaks every hour.",
        tags=("energy",),
    )
    knowledge_client = Mock()
    knowledge_client.search = AsyncMock(return_value=[hit])
    real_summary = TemplateDaySummaryClient()
    summary_client = AsyncMock(wraps=real_summary)
    summary_client.build = AsyncMock(side_effect=real_summary.build)

    repository: Any = Mock()
    repository.get_checkin_by_id = AsyncMock(return_value=checkin)
    repository.save_checkin = AsyncMock(return_value=checkin)
    processor = DaySummaryProcessor(
        repository=repository,
        summary_client=summary_client,
        knowledge_client=knowledge_client,
    )

    await processor.process_checkin(checkin_id=checkin_id)

    knowledge_client.search.assert_awaited_once()
    assert "Meetings" in knowledge_client.search.await_args.args[0]
    build_kwargs = summary_client.build.await_args.kwargs
    assert build_kwargs["knowledge_chunks"] == [hit]
    assert checkin.artifact_status == ArtifactStatus.READY


@pytest.mark.asyncio
async def test_day_summary_processor_continues_when_knowledge_fails() -> None:
    checkin_id, checkin = _sample_checkin()
    knowledge_client = Mock()
    knowledge_client.search = AsyncMock(side_effect=KnowledgeSearchError("down"))
    repository: Any = Mock()
    repository.get_checkin_by_id = AsyncMock(return_value=checkin)
    repository.save_checkin = AsyncMock(return_value=checkin)
    processor = DaySummaryProcessor(
        repository=repository,
        summary_client=TemplateDaySummaryClient(),
        knowledge_client=knowledge_client,
    )

    await processor.process_checkin(checkin_id=checkin_id)

    assert checkin.artifact is not None
    assert checkin.artifact_status == ArtifactStatus.READY
    repository.save_checkin.assert_awaited_once()


@pytest.mark.asyncio
async def test_day_summary_processor_skips_when_artifact_exists() -> None:
    checkin_id = uuid4()
    checkin = DailyCheckin(
        id=checkin_id,
        user_id=uuid4(),
        status=CheckinStatus.ANSWERED,
        stress_level=3,
        energy_level=3,
        plan_done=3,
        blocker_present=0,
        learning_done=3,
        artifact=DailyArtifact(
            structured_summary_json={"day_summary": "done"},
            source=ArtifactSource.TEMPLATE,
        ),
    )
    checkin.artifact_status = ArtifactStatus.READY
    repository: Any = Mock()
    repository.get_checkin_by_id = AsyncMock(return_value=checkin)
    repository.save_checkin = AsyncMock()
    processor = DaySummaryProcessor(
        repository=repository,
        summary_client=TemplateDaySummaryClient(),
        knowledge_client=_disabled_knowledge_client(),
    )

    await processor.process_checkin(checkin_id=checkin_id)

    repository.save_checkin.assert_not_awaited()
