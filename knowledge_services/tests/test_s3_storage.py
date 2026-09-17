from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from knowledge_services.core.storage.s3 import S3ObjectStorage
from knowledge_services.core.storage.session import s3_client_kwargs, s3_client_scope


def _client_error(code: str) -> ClientError:
    return ClientError(
        error_response={"Error": {"Code": code, "Message": "missing"}},
        operation_name="HeadBucket",
    )


class _FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    async def __aenter__(self) -> "_FakeBody":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def read(self) -> bytes:
        return self._data


class _FakeClientContext:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def __aenter__(self) -> Any:
        return self._client

    async def __aexit__(self, *args: object) -> None:
        return None


@pytest.fixture
def client() -> MagicMock:
    mock = MagicMock()
    mock.head_bucket = AsyncMock()
    mock.create_bucket = AsyncMock()
    mock.put_object = AsyncMock()
    mock.get_object = AsyncMock(return_value={"Body": _FakeBody(b"hello")})
    mock.delete_object = AsyncMock()
    return mock


@pytest.fixture
def storage(client: MagicMock) -> S3ObjectStorage:
    return S3ObjectStorage(client, bucket="knowledge", region="us-east-1")


@pytest.mark.asyncio
async def test_ensure_bucket_creates_when_missing(storage: S3ObjectStorage, client: MagicMock) -> None:
    client.head_bucket = AsyncMock(side_effect=_client_error("404"))

    await storage.ensure_bucket()

    client.head_bucket.assert_awaited_once_with(Bucket="knowledge")
    client.create_bucket.assert_awaited_once_with(Bucket="knowledge")


@pytest.mark.asyncio
async def test_ensure_bucket_skips_when_exists(storage: S3ObjectStorage, client: MagicMock) -> None:
    await storage.ensure_bucket()
    client.create_bucket.assert_not_awaited()


@pytest.mark.asyncio
async def test_put_get_delete_bytes(storage: S3ObjectStorage, client: MagicMock) -> None:
    key = await storage.put_bytes("docs/a.md", b"hello", content_type="text/markdown")
    data = await storage.get_bytes("docs/a.md")
    await storage.delete("docs/a.md")

    assert key == "docs/a.md"
    assert data == b"hello"
    client.put_object.assert_awaited_once_with(
        Bucket="knowledge",
        Key="docs/a.md",
        Body=b"hello",
        ContentType="text/markdown",
    )
    client.delete_object.assert_awaited_once_with(Bucket="knowledge", Key="docs/a.md")


def test_s3_client_kwargs_use_path_style() -> None:
    kwargs = s3_client_kwargs(
        endpoint_url="http://localhost:9000",
        access_key="test",
        secret_key="test",
        region="us-east-1",
        force_path_style=True,
    )
    assert kwargs["endpoint_url"] == "http://localhost:9000"
    assert kwargs["aws_access_key_id"] == "test"
    assert kwargs["config"].s3 == {"addressing_style": "path"}


@pytest.mark.asyncio
async def test_s3_client_scope_yields_client() -> None:
    fake_client = object()
    session = MagicMock()
    session.client = MagicMock(return_value=_FakeClientContext(fake_client))

    with patch("knowledge_services.core.storage.session.aioboto3.Session", return_value=session):
        async with s3_client_scope(
            endpoint_url="http://localhost:9000",
            access_key="test",
            secret_key="test",
        ) as client:
            assert client is fake_client
