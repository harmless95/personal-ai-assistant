from typing import Any

from knowledge_services import KnowledgeChunk
from knowledge_services.core.data.repository import KnowledgeChunkRepository
from knowledge_services.core.embeddings.protocol import Embedder
from knowledge_services.core.ingest.chunking import split_text


class IngestService:
    def __init__(
        self,
        *,
        embedder: Embedder,
        repository: KnowledgeChunkRepository,
    ) -> None:
        self._embedder = embedder
        self._repository = repository

    async def ingest_text(
        self,
        text: str,
        *,
        source: str,
        tags: list[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> list[KnowledgeChunk]:
        pieces = split_text(text)
        if not pieces:
            return []

        vectors = await self._embedder.embed_many(pieces)

        saved: list[KnowledgeChunk] = []
        for index, (piece, vector) in enumerate(zip(pieces, vectors, strict=True), start=1):
            chunk = await self._repository.add_chunk(
                source=source,
                chunk_index=index,
                text=piece,
                embedding=vector,
                tags=tags,
                meta=meta,
            )
            saved.append(chunk)
        return saved
