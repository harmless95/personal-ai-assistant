from collections.abc import Sequence
from typing import Protocol


class Embedder(Protocol):
    """Convert text to a fixed-size embedding vector."""

    async def embed(self, text: str) -> list[float]:
        """Return one embedding; length must match EMBEDDING_DIMENSIONS."""
        ...

    async def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        """Return embeddings in the same order as texts."""
        ...
