from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import grpc
import pytest

from app.knowledge import get_knowledge_client
from app.knowledge.client import KnowledgeGrpcClient, KnowledgeSearchError


@pytest.mark.asyncio
async def test_search_returns_mapped_chunks() -> None:
    chunk = SimpleNamespace(
        chunk_id="c1",
        source="doc.md",
        chunk_index=1,
        text="hello world",
        tags=["a", "b"],
    )
    response = SimpleNamespace(chunks=[chunk])
    stub = MagicMock()
    stub.Search = AsyncMock(return_value=response)

    channel = MagicMock()
    channel.__aenter__ = AsyncMock(return_value=channel)
    channel.__aexit__ = AsyncMock(return_value=None)

    client = KnowledgeGrpcClient(target="localhost:50051", top_k=2, enabled=True)
    with (
        patch("app.knowledge.client.grpc.aio.insecure_channel", return_value=channel),
        patch(
            "app.knowledge.client.knowledge_pb2_grpc.KnowledgeServiceStub",
            return_value=stub,
        ),
    ):
        hits = await client.search("  how to start  ")

    assert len(hits) == 1
    assert hits[0].chunk_id == "c1"
    assert hits[0].source == "doc.md"
    assert hits[0].chunk_index == 1
    assert hits[0].text == "hello world"
    assert hits[0].tags == ("a", "b")
    stub.Search.assert_awaited_once()
    request = stub.Search.await_args.args[0]
    assert request.query == "how to start"
    assert request.top_k == 2


@pytest.mark.asyncio
async def test_search_disabled_returns_empty() -> None:
    client = KnowledgeGrpcClient(target="localhost:50051", enabled=False)
    assert await client.search("anything") == []


@pytest.mark.asyncio
async def test_search_blank_query_returns_empty() -> None:
    client = KnowledgeGrpcClient(target="localhost:50051", enabled=True)
    assert await client.search("   ") == []


@pytest.mark.asyncio
async def test_search_wraps_rpc_error() -> None:
    rpc_error = grpc.aio.AioRpcError(
        code=grpc.StatusCode.UNAVAILABLE,
        initial_metadata=None,
        trailing_metadata=None,
        details="connection refused",
    )
    stub = MagicMock()
    stub.Search = AsyncMock(side_effect=rpc_error)
    channel = MagicMock()
    channel.__aenter__ = AsyncMock(return_value=channel)
    channel.__aexit__ = AsyncMock(return_value=None)

    client = KnowledgeGrpcClient(target="localhost:50051", enabled=True)
    with (
        patch("app.knowledge.client.grpc.aio.insecure_channel", return_value=channel),
        patch(
            "app.knowledge.client.knowledge_pb2_grpc.KnowledgeServiceStub",
            return_value=stub,
        ),
        pytest.raises(KnowledgeSearchError, match="UNAVAILABLE"),
    ):
        await client.search("query")


def test_get_knowledge_client_uses_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.knowledge.settings.knowledge.enabled", False)
    monkeypatch.setattr("app.knowledge.settings.knowledge.grpc_target", "knowledge:50051")
    monkeypatch.setattr("app.knowledge.settings.knowledge.top_k", 5)
    monkeypatch.setattr("app.knowledge.settings.knowledge.timeout_seconds", 1.5)

    client = get_knowledge_client()
    assert client._enabled is False
    assert client._target == "knowledge:50051"
    assert client._top_k == 5
    assert client._timeout_seconds == 1.5
