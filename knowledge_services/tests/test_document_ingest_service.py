from collections.abc import Sequence
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from knowledge_services.core.ingest.document_service import DocumentIngestService
from knowledge_services.db.constants import EMBEDDING_DIMENSIONS
from knowledge_services.db.models import KnowledgeChunk
from knowledge_services.tests.fakes import FakeEmbedder


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.ensure_bucket = AsyncMock()

    async def put_bytes(
        self,
        key: str,
        body: bytes,
        *,
        content_type: str = "application/octet-stream",
    ) -> str:
        self.objects[key] = (body, content_type)
        return key

    async def get_bytes(self, key: str) -> bytes:
        return self.objects[key][0]

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)


@pytest.mark.asyncio
async def test_ingest_file_stores_s3_and_saves_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "knowledge_services.core.ingest.service.split_text",
        lambda _text: ["piece one", "piece two"],
    )

    async def _add_chunks(chunks: Sequence[KnowledgeChunk]) -> list[KnowledgeChunk]:
        return list(chunks)

    repository = Mock()
    repository.add_chunks = AsyncMock(side_effect=_add_chunks)
    storage = FakeStorage()
    service = DocumentIngestService(
        embedder=FakeEmbedder(),
        repository=repository,
        storage=storage,
    )

    content = b"hello from file"
    chunks, s3_key = await service.ingest_file(
        content,
        source="notes/demo.md",
        content_type="text/markdown",
        tags=["demo"],
    )

    assert s3_key.startswith("documents/")
    assert s3_key.endswith("notes/demo.md")
    assert storage.objects[s3_key] == (content, "text/markdown")
    storage.ensure_bucket.assert_awaited_once()
    assert len(chunks) == 2
    assert chunks[0].source == "notes/demo.md"
    assert chunks[0].meta["s3_key"] == s3_key
    assert chunks[0].meta["content_type"] == "text/markdown"
    assert chunks[0].tags == ["demo"]
    assert len(chunks[0].embedding) == EMBEDDING_DIMENSIONS


@pytest.mark.asyncio
async def test_ingest_from_s3_reads_stored_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "knowledge_services.core.ingest.service.split_text",
        lambda _text: ["only"],
    )

    async def _add_chunks(chunks: Sequence[KnowledgeChunk]) -> list[KnowledgeChunk]:
        for chunk in chunks:
            chunk.id = uuid4()
        return list(chunks)

    repository = Mock()
    repository.add_chunks = AsyncMock(side_effect=_add_chunks)
    storage = FakeStorage()
    key = "documents/abc/demo.md"
    await storage.put_bytes(key, b"stored text", content_type="text/plain")

    service = DocumentIngestService(
        embedder=FakeEmbedder(),
        repository=repository,
        storage=storage,
    )
    chunks = await service.ingest_from_s3(key, source="demo.md")

    assert len(chunks) == 1
    assert chunks[0].text == "only"
    assert chunks[0].meta["s3_key"] == key


@pytest.mark.asyncio
async def test_ingest_file_rejects_empty_content() -> None:
    service = DocumentIngestService(
        embedder=FakeEmbedder(),
        repository=Mock(),
        storage=FakeStorage(),
    )
    with pytest.raises(ValueError, match="content"):
        await service.ingest_file(b"", source="x.md")
