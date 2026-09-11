from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_services.db.models import KnowledgeChunk


class KnowledgeChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def add_chunks(self, chunks: Sequence[KnowledgeChunk]) -> list[KnowledgeChunk]:
        self.__session.add_all(chunks)
        await self.__session.flush()
        return list(chunks)

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
