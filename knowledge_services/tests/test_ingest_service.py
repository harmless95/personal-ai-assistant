from typing import Any
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from knowledge_services.core.ingest.service import IngestService
from knowledge_services.db.constants import EMBEDDING_DIMENSIONS
from knowledge_services.db.models import KnowledgeChunk
from knowledge_services.tests.fakes import FakeEmbedder


def _chunk(
    *,
    source: str,
    chunk_index: int,
    text: str,
    embedding: list[float],
) -> KnowledgeChunk:
    return KnowledgeChunk(
        id=uuid4(),
        source=source,
        chunk_index=chunk_index,
        text=text,
        embedding=embedding,
        tags=[],
        meta={},
    )


@pytest.mark.asyncio
async def test_ingest_text_empty_returns_empty() -> None:
    repository = Mock()
    repository.add_chunk = AsyncMock()
    service = IngestService(embedder=FakeEmbedder(), repository=repository)

    assert await service.ingest_text("   ", source="empty.md") == []
    repository.add_chunk.assert_not_awaited()


@pytest.mark.asyncio
async def test_ingest_text_saves_chunks_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    pieces = ["first piece", "second piece"]
    monkeypatch.setattr(
        "knowledge_services.core.ingest.service.split_text",
        lambda _text: pieces,
    )

    saved: list[dict[str, Any]] = []

    async def _add_chunk(**kwargs: Any) -> KnowledgeChunk:
        saved.append(kwargs)
        return _chunk(
            source=kwargs["source"],
            chunk_index=kwargs["chunk_index"],
            text=kwargs["text"],
            embedding=kwargs["embedding"],
        )

    repository = Mock()
    repository.add_chunk = AsyncMock(side_effect=_add_chunk)
    embedder = FakeEmbedder()
    service = IngestService(embedder=embedder, repository=repository)

    result = await service.ingest_text(
        "ignored because split is patched",
        source="demo.md",
        tags=["python"],
        meta={"title": "Demo"},
    )

    assert len(result) == 2
    assert saved[0]["source"] == "demo.md"
    assert saved[0]["chunk_index"] == 1
    assert saved[0]["text"] == "first piece"
    assert saved[0]["tags"] == ["python"]
    assert saved[0]["meta"] == {"title": "Demo"}
    assert len(saved[0]["embedding"]) == EMBEDDING_DIMENSIONS
    assert saved[1]["chunk_index"] == 2
    assert saved[1]["text"] == "second piece"
    assert saved[0]["embedding"] != saved[1]["embedding"]
