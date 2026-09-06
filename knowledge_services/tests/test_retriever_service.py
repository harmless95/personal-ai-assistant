from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from knowledge_services import KnowledgeChunk
from knowledge_services.core.retrievers.service import RetrieverService
from knowledge_services.db.constants import EMBEDDING_DIMENSIONS
from knowledge_services.tests.fakes import FakeEmbedder


@pytest.mark.asyncio
async def test_search_blank_query_returns_empty() -> None:
    repository = Mock()
    repository.search_by_embedding = AsyncMock()
    service = RetrieverService(embedder=FakeEmbedder(), repository=repository)

    assert await service.search("   ") == []
    assert await service.search("query", top_k=0) == []
    repository.search_by_embedding.assert_not_awaited()


@pytest.mark.asyncio
async def test_search_embeds_query_and_delegates_to_repository() -> None:
    hit = KnowledgeChunk(
        id=uuid4(),
        source="demo.md",
        chunk_index=1,
        text="Asyncio create_task starts a coroutine.",
        embedding=[0.0] * EMBEDDING_DIMENSIONS,
        tags=[],
        meta={},
    )
    repository = Mock()
    repository.search_by_embedding = AsyncMock(return_value=[hit])
    embedder = FakeEmbedder()
    service = RetrieverService(embedder=embedder, repository=repository)

    query = "How do I start a coroutine?"
    result = await service.search(query, top_k=2)

    assert result == [hit]
    expected_vector = await embedder.embed(query)
    repository.search_by_embedding.assert_awaited_once_with(expected_vector, top_k=2)
