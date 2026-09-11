from collections.abc import Sequence
from unittest.mock import AsyncMock, Mock

import pytest

from knowledge_services.core.ingest.service import IngestService
from knowledge_services.db.constants import EMBEDDING_DIMENSIONS
from knowledge_services.db.models import KnowledgeChunk
from knowledge_services.tests.fakes import FakeEmbedder


@pytest.mark.asyncio
async def test_ingest_text_empty_returns_empty() -> None:
    repository = Mock()
    repository.add_chunks = AsyncMock()
    service = IngestService(embedder=FakeEmbedder(), repository=repository)

    assert await service.ingest_text("   ", source="empty.md") == []
    repository.add_chunks.assert_not_awaited()


@pytest.mark.asyncio
async def test_ingest_text_saves_chunks_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    pieces = ["first piece", "second piece"]
    monkeypatch.setattr(
        "knowledge_services.core.ingest.service.split_text",
        lambda _text: pieces,
    )

    async def _add_chunks(chunks: Sequence[KnowledgeChunk]) -> list[KnowledgeChunk]:
        return list(chunks)

    repository = Mock()
    repository.add_chunks = AsyncMock(side_effect=_add_chunks)
    embedder = FakeEmbedder()
    service = IngestService(embedder=embedder, repository=repository)

    result = await service.ingest_text(
        "ignored because split is patched",
        source="demo.md",
        tags=["python"],
        meta={"title": "Demo"},
    )

    repository.add_chunks.assert_awaited_once()
    saved = repository.add_chunks.await_args.args[0]
    assert result == list(saved)
    assert len(saved) == 2
    assert saved[0].source == "demo.md"
    assert saved[0].chunk_index == 1
    assert saved[0].text == "first piece"
    assert saved[0].tags == ["python"]
    assert saved[0].meta == {"title": "Demo"}
    assert len(saved[0].embedding) == EMBEDDING_DIMENSIONS
    assert saved[1].chunk_index == 2
    assert saved[1].text == "second piece"
    assert saved[0].embedding != saved[1].embedding


@pytest.mark.asyncio
async def test_ingest_text_defaults_empty_tags_and_meta(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "knowledge_services.core.ingest.service.split_text",
        lambda _text: ["only piece"],
    )

    async def _add_chunks(chunks: Sequence[KnowledgeChunk]) -> list[KnowledgeChunk]:
        return list(chunks)

    repository = Mock()
    repository.add_chunks = AsyncMock(side_effect=_add_chunks)
    service = IngestService(embedder=FakeEmbedder(), repository=repository)

    await service.ingest_text("ignored", source="demo.md")

    saved = repository.add_chunks.await_args.args[0]
    assert saved[0].tags == []
    assert saved[0].meta == {}
