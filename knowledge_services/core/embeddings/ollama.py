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
        response = await self._client.post(
            "/api/embeddings",
            json={"model": self._model, "prompt": text},
        )
        response.raise_for_status()
        embedding = response.json()["embedding"]
        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise ValueError(f"expected {EMBEDDING_DIMENSIONS} dims, got {len(embedding)}")
        return list(embedding)

    async def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        return [await self.embed(text) for text in texts]
