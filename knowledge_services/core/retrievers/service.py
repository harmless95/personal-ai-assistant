from knowledge_services import KnowledgeChunk
from knowledge_services.core.data.repository import KnowledgeChunkRepository
from knowledge_services.core.embeddings.protocol import Embedder


class RetrieverService:
    def __init__(
        self,
        *,
        embedder: Embedder,
        repository: KnowledgeChunkRepository,
    ) -> None:
        self._embedder = embedder
        self._repository = repository

    async def search(
        self,
        query: str,
        *,
        top_k: int = 3,
    ) -> list[KnowledgeChunk]:
        cleaned = query.strip()
        if not cleaned or top_k <= 0:
            return []

        vector = await self._embedder.embed(cleaned)
        return await self._repository.search_by_embedding(vector, top_k=top_k)
