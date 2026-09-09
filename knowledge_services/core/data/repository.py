from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_services.db.models import KnowledgeChunk


class KnowledgeChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def add_chunk(
        self,
        *,
        source: str,
        chunk_index: int,
        text: str,
        embedding: list[float],
        tags: list[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> KnowledgeChunk:
        chunk = KnowledgeChunk(
            source=source,
            chunk_index=chunk_index,
            text=text,
            embedding=embedding,
            tags=tags or [],
            meta=meta or {},
        )
        self.__session.add(chunk)
        await self.__session.flush()
        return chunk

    async def search_by_embedding(
        self,
        embedding: list[float],
        *,
        top_k: int = 3,
    ) -> list[KnowledgeChunk]:
        if top_k <= 0:
            return []
        distance = KnowledgeChunk.embedding.cosine_distance(embedding)
        stmt = select(KnowledgeChunk).order_by(distance).limit(top_k)
        result = await self.__session.execute(stmt)
        return list(result.scalars().all())
