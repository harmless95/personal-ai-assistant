from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import grpc
import pytest

from app.knowledge.client import KnowledgeGrpcClient, KnowledgeIngestError


@pytest.mark.asyncio
async def test_ingest_file_returns_result() -> None:
    response = SimpleNamespace(chunks_saved=3, s3_key="documents/abc/notes.md")
    stub = MagicMock()
    stub.IngestFile = AsyncMock(return_value=response)
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
    ):
        result = await client.ingest_file(
            b"hello",
            source="notes.md",
            content_type="text/markdown",
            tags=["demo"],
        )

    assert result.chunks_saved == 3
    assert result.s3_key == "documents/abc/notes.md"
    request = stub.IngestFile.await_args.args[0]
    assert request.content == b"hello"
    assert request.source == "notes.md"
    assert request.content_type == "text/markdown"
    assert list(request.tags) == ["demo"]


@pytest.mark.asyncio
async def test_ingest_file_disabled_raises() -> None:
    client = KnowledgeGrpcClient(target="localhost:50051", enabled=False)
    with pytest.raises(KnowledgeIngestError, match="disabled"):
        await client.ingest_file(b"x", source="a.md")


@pytest.mark.asyncio
async def test_ingest_file_wraps_rpc_error() -> None:
    rpc_error = grpc.aio.AioRpcError(
        code=grpc.StatusCode.UNAVAILABLE,
        initial_metadata=None,
        trailing_metadata=None,
        details="down",
    )
    stub = MagicMock()
    stub.IngestFile = AsyncMock(side_effect=rpc_error)
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
        pytest.raises(KnowledgeIngestError, match="UNAVAILABLE"),
    ):
        await client.ingest_file(b"x", source="a.md")
