from typing import Any
from uuid import uuid4

from knowledge_services.core.data.repository import KnowledgeChunkRepository
from knowledge_services.core.embeddings.protocol import Embedder
from knowledge_services.core.ingest.service import IngestService
from knowledge_services.core.storage.protocol import ObjectStorage
from knowledge_services.db.models import KnowledgeChunk


class DocumentIngestService:
    """Store original bytes in S3, then chunk/embed via IngestService."""

    def __init__(
        self,
        *,
        embedder: Embedder,
        repository: KnowledgeChunkRepository,
        storage: ObjectStorage,
    ) -> None:
        self._storage = storage
        self._ingest = IngestService(embedder=embedder, repository=repository)

    async def ingest_file(
        self,
        content: bytes,
        *,
        source: str,
        content_type: str = "text/plain",
        tags: list[str] | None = None,
        encoding: str = "utf-8",
    ) -> tuple[list[KnowledgeChunk], str]:
        if not content:
            raise ValueError("content must be non-empty")
        if not source.strip():
            raise ValueError("source must be non-empty")

        s3_key = _build_object_key(source)
        await self._storage.ensure_bucket()
        await self._storage.put_bytes(s3_key, content, content_type=content_type)

        text = content.decode(encoding)
        meta: dict[str, Any] = {
            "s3_key": s3_key,
            "content_type": content_type,
        }
        chunks = await self._ingest.ingest_text(
            text,
            source=source.strip(),
            tags=tags,
            meta=meta,
        )
        return chunks, s3_key

    async def ingest_from_s3(
        self,
        s3_key: str,
        *,
        source: str,
        tags: list[str] | None = None,
        encoding: str = "utf-8",
        content_type: str = "text/plain",
    ) -> list[KnowledgeChunk]:
        content = await self._storage.get_bytes(s3_key)
        text = content.decode(encoding)
        return await self._ingest.ingest_text(
            text,
            source=source.strip(),
            tags=tags,
            meta={"s3_key": s3_key, "content_type": content_type},
        )


def _build_object_key(source: str) -> str:
    safe = source.replace("\\", "/").strip().lstrip("/")
    return f"documents/{uuid4().hex}/{safe}"
