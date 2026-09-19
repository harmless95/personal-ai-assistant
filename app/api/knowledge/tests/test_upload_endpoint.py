from io import BytesIO
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.auth.deps import get_current_user
from app.db import User
from app.knowledge import KnowledgeIngestError, get_knowledge_client
from app.knowledge.models import KnowledgeIngestFileResult
from app.main import app

client_test = TestClient(app=app)


def _make_user() -> User:
    return User(
        id=uuid4(),
        email="user@example.com",
        name="Test",
        surname="User",
        hashed_password="hash",
    )


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_upload_knowledge_file_endpoint() -> None:
    user = _make_user()
    knowledge = AsyncMock()
    knowledge.ingest_file = AsyncMock(
        return_value=KnowledgeIngestFileResult(chunks_saved=2, s3_key="documents/x/notes.md"),
    )
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_knowledge_client] = lambda: knowledge

    try:
        response = client_test.post(
            "/api/v1/knowledge/upload/",
            files={"file": ("notes.md", BytesIO(b"# hello"), "text/markdown")},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["chunks_saved"] == 2
    assert body["s3_key"] == "documents/x/notes.md"
    assert body["source"] == "notes.md"
    knowledge.ingest_file.assert_awaited_once()


def test_upload_knowledge_file_maps_ingest_error() -> None:
    user = _make_user()
    knowledge = AsyncMock()
    knowledge.ingest_file = AsyncMock(side_effect=KnowledgeIngestError("boom"))
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_knowledge_client] = lambda: knowledge

    try:
        response = client_test.post(
            "/api/v1/knowledge/upload/",
            files={"file": ("notes.md", BytesIO(b"hi"), "text/plain")},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 502
    assert "boom" in response.json()["detail"]
