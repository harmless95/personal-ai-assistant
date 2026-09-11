from collections.abc import Sequence

import httpx

from knowledge_services.config import settings
from knowledge_services.db.constants import EMBEDDING_DIMENSIONS


class OllamaEmbedder:
    def __init__(
        self,
        *,
        base_url: str = settings.rag.ollama_base_url,
        model: str = settings.rag.embed_model,
        timeout: float = 60.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def embed(self, text: str) -> list[float]:
        vectors = await self.embed_many([text])
        return vectors[0]

    async def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self._client.post(
            "/api/embed",
            json={"model": self._model, "input": list(texts)},
        )
        response.raise_for_status()
        embeddings = response.json()["embeddings"]
        if len(embeddings) != len(texts):
            raise ValueError(f"expected {len(texts)} embeddings, got {len(embeddings)}")
        result: list[list[float]] = []
        for embedding in embeddings:
            if len(embedding) != EMBEDDING_DIMENSIONS:
                raise ValueError(f"expected {EMBEDDING_DIMENSIONS} dims, got {len(embedding)}")
            result.append(list(embedding))
        return result
