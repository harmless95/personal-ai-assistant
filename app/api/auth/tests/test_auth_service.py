from datetime import datetime, timedelta, timezone
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID

import jwt
import pytest
from fastapi import HTTPException
from jwt import ExpiredSignatureError, InvalidTokenError

from app.api.auth.models.token import TokenPayload, TokenResponse, TokenScope
from app.api.auth.models.user import RegisterRequest
from app.api.auth.services.auth_service import AuthService
from app.db import User


@pytest.fixture
def token_repository_mock() -> Any:
    mock_repo = MagicMock()
    mock_repo.create_refresh_token = AsyncMock()
    mock_repo.revoke_token = AsyncMock()
    return mock_repo


@pytest.fixture
def user_repository_empty(user: User) -> Any:
    user_repository = Mock()
    user_repository.create_user = AsyncMock()
    user_repository.get_user_by_email = AsyncMock()

    user_repository.create_user.return_value = user
    user_repository.get_user_by_email.return_value = None

    return user_repository


@pytest.fixture
def auth_service(token_repository_mock: Any, user_repository_empty: Any) -> AuthService:
    return AuthService(token_repository=token_repository_mock, user_repository=user_repository_empty)


@pytest.fixture
def user_repository_with_user(user: User) -> Any:
    user_repository = Mock()
    user_repository.create_user = AsyncMock()
    user_repository.get_user_by_email = AsyncMock()

    user_repository.get_user_by_email.return_value = user

    return user_repository


def test_auth_token_service_success() -> None:
    exp_time = (datetime.now(timezone.utc) + timedelta(hours=1)).replace(microsecond=0)
    fake_payload = TokenPayload(sub=UUID("16e105d1-83b2-409d-8dbf-43fb0fd94bd5"), exp=exp_time, scope=TokenScope.ACCESS)

    secret_key = "7a8f9c1e3b5d7f9a0b2c4d6e8f0a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a"
    algorithm = "HS256"

    encode_token = jwt.encode(payload=fake_payload.to_jwt_dict(), key=secret_key, algorithm=algorithm)
    assert isinstance(encode_token, str)
    assert len(encode_token.split(".")) == 3

    decode_token = TokenPayload.from_jwt(token=encode_token, secret=secret_key, algorithm=algorithm)
    assert decode_token.sub == fake_payload.sub
    assert decode_token.exp == fake_payload.exp


def test_auth_token_service_expired() -> None:
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    expired_payload = TokenPayload(
        sub=UUID("16e105d1-83b2-409d-8dbf-43fb0fd94bd5"), exp=past_time, scope=TokenScope.ACCESS
    )
    secret_key = "7a8f9c1e3b5d7f9a0b2c4d6e8f0a1b3c5d7e9f0a2b4c6d8e0f1a3b5c7d9e1f2a"

    token = jwt.encode(payload=expired_payload.to_jwt_dict(), key=secret_key)

    with pytest.raises(ExpiredSignatureError):
        TokenPayload.from_jwt(token=token, secret=secret_key)


@pytest.mark.asyncio
async def test_validate_payload_success() -> None:
    exp_time = datetime.now(timezone.utc) + timedelta(hours=1)
    fake_payload = TokenPayload(sub=UUID("16e105d1-83b2-409d-8dbf-43fb0fd94bd5"), exp=exp_time, scope=TokenScope.ACCESS)

    with patch("app.api.auth.services.auth_service.TokenPayload.from_jwt") as mock_token_service:
        mock_token_service.return_value = fake_payload
        result = await AuthService.validate_payload("valid_token")

        assert result == fake_payload


@pytest.mark.asyncio
async def test_auth_service_flow() -> None:
    user_id = UUID("16e105d1-83b2-409d-8dbf-43fb0fd94bd5")
    fake_token = "header.payload.signature"

    with patch("app.api.auth.services.auth_service.asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
        mock_to_thread.return_value = fake_token

        token = await AuthService._create_access_token(user_id=user_id)

        assert token == fake_token
        mock_to_thread.assert_called_once()

    with patch("app.api.auth.services.auth_service.TokenPayload.from_jwt") as mock_from_jwt:
        mock_from_jwt.side_effect = InvalidTokenError()

        with pytest.raises(HTTPException) as exc:
            await AuthService.validate_payload("wrong_token")

        assert exc.value.status_code == 401
        detail = cast(dict[str, str], exc.value.detail)
        assert detail == {"id": "token_invalid", "message": "Invalid token"}


@pytest.mark.asyncio
async def test_get_login_token(user: User, auth_service: AuthService) -> None:
    with (
        patch(
            "app.api.auth.services.auth_service.AuthService._create_access_token", AsyncMock(return_value="fake_token")
        ),
        patch.object(AuthService, "_create_refresh_token", AsyncMock(return_value="fake_token")),
    ):
        auth_data = await auth_service.get_tokens(user_id=user.id)
        token_info = auth_data.model_dump()
        assert token_info.get("access_token") == "fake_token"
        assert token_info.get("token_type") == "Bearer"


@patch("app.api.auth.services.auth_service.PasswordUtils.hash_password", return_value="mocked_hashed_password")
@pytest.mark.asyncio
async def test_register(mock_hash_password: Any, user_repository_empty: Any, auth_service: AuthService) -> None:
    new_user = await auth_service.register_new_user(
        RegisterRequest(email="some@example.com", password="Test123!!!!!!", name="name", surname="surname"),
    )

    mock_hash_password.assert_called_once_with(password="Test123!!!!!!")
    user_repository_empty.create_user.assert_called_once_with(
        email="some@example.com", hashed_password="mocked_hashed_password", name="name", surname="surname"
    )

    assert new_user.id == UUID("16e105d1-83b2-409d-8dbf-43fb0fd94bd5")
    assert new_user.created_at == datetime(2020, 1, 20, 0, 0)


@pytest.mark.asyncio
async def test_register_with_existing_user(auth_service: AuthService, user_repository_with_user: Any) -> None:
    auth_service.user_repo = user_repository_with_user
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register_new_user(
            RegisterRequest(email="some@example.com", password="Test123!!!!!!", name="name", surname="surname"),
        )

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_refresh_access_success(auth_service: AuthService) -> None:
    fake_refresh_token = "valid.refresh.token"
    fake_hash = "hashed_refresh_token"
    user_id = UUID("16e105d1-83b2-409d-8dbf-43fb0fd94bd5")

    mock_payload = TokenPayload(sub=user_id, exp=datetime.now(timezone.utc), scope=TokenScope.REFRESH)
    mock_db_token = MagicMock()
    expected_response = TokenResponse(access_token="new_access_token", refresh_token="new_refresh_token")

    with (
        patch(
            "app.api.auth.services.auth_service.AuthService.validate_payload", AsyncMock(return_value=mock_payload)
        ) as mock_validate,
        patch("app.api.auth.services.auth_service.TokenCryptoUtils.hash_token", return_value=fake_hash) as mock_hash,
        patch.object(AuthService, "get_tokens", AsyncMock(return_value=expected_response)) as mock_get_tokens,
        patch.object(auth_service.token_repo, "revoke_token", AsyncMock(return_value=mock_db_token)) as mock_revoke,
    ):
        result = await auth_service.refresh_access(refresh_token=fake_refresh_token)

        assert result == expected_response
        mock_validate.assert_awaited_once_with(token=fake_refresh_token)
        mock_hash.assert_called_once_with(token=fake_refresh_token)
        mock_get_tokens.assert_awaited_once_with(user_id=user_id)
        mock_revoke.assert_awaited_once_with(user_id=user_id, token=fake_hash)


@pytest.mark.asyncio
async def test_refresh_access_token_not_found_raises_exception(auth_service: AuthService) -> None:
    fake_refresh_token = "invalid.or.revoked.token"
    fake_hash = "hashed_invalid_token"
    user_id = UUID("16e105d1-83b2-409d-8dbf-43fb0fd94bd5")
    mock_payload = TokenPayload(sub=user_id, exp=datetime.now(timezone.utc), scope=TokenScope.REFRESH)

    with (
        patch("app.api.auth.services.auth_service.AuthService.validate_payload", AsyncMock(return_value=mock_payload)),
        patch("app.api.auth.services.auth_service.TokenCryptoUtils.hash_token", return_value=fake_hash),
        patch("app.api.auth.services.auth_service.AuthService.get_tokens", AsyncMock()) as mock_get_tokens,
        patch.object(auth_service.token_repo, "revoke_token", AsyncMock(return_value=None)) as mock_revoke,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh_access(refresh_token=fake_refresh_token)

        assert exc_info.value.status_code == 401
        detail = cast(dict[str, str], exc_info.value.detail)
        assert detail == {"id": "token_not_found", "message": "Token not found or already revoked"}
        mock_get_tokens.assert_not_awaited()
        mock_revoke.assert_awaited_once_with(user_id=user_id, token=fake_hash)
