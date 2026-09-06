from collections.abc import Sequence

import pytest

from knowledge_services.db.constants import EMBEDDING_DIMENSIONS
from knowledge_services.tests.fakes import FakeEmbedder


@pytest.mark.asyncio
async def test_fake_embedder_dimensions_and_order() -> None:
    embedder = FakeEmbedder()
    texts: Sequence[str] = ("alpha", "beta")
    vectors = await embedder.embed_many(texts)

    assert len(vectors) == 2
    assert all(len(vector) == EMBEDDING_DIMENSIONS for vector in vectors)
    assert vectors[0] == await embedder.embed("alpha")
    assert vectors[0] != vectors[1]
