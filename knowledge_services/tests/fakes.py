from collections.abc import Sequence

from knowledge_services.db.constants import EMBEDDING_DIMENSIONS


class FakeEmbedder:
    """Deterministic embedder for unit tests (no Ollama)."""

    async def embed(self, text: str) -> list[float]:
        seed = sum(ord(char) for char in text) % 97
        return [float((seed + index) % 97) / 97.0 for index in range(EMBEDDING_DIMENSIONS)]

    async def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        return [await self.embed(text) for text in texts]
