import asyncio
from typing import Annotated

import structlog
from fastapi import Body, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.data.token_repository import TokenRepository
from app.api.auth.data.user_repository import UserRepository
from app.api.auth.errors import AuthErrors, LogEvents
from app.api.auth.models.token import TokenScope
from app.api.auth.services.auth_service import AuthService
from app.api.auth.utils.password import PasswordUtils
from app.api.auth.utils.token import TokenCryptoUtils
from app.config import settings
from app.db import User
from app.db.session import session_getter

logger = structlog.get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix_v1}/auth/login")
TokenDep = Annotated[str, Depends(oauth2_scheme)]
UserPasswordRequestFormDep = Annotated[OAuth2PasswordRequestForm, Depends()]
SessionDep = Annotated[AsyncSession, Depends(session_getter)]
RefreshTokenDep = Annotated[str, Body(alias="refresh_token")]


def get_auth_service(
    session: SessionDep,
) -> AuthService:
    token_repo = TokenRepository(session=session)
    user_repo = UserRepository(session=session)
    return AuthService(token_repository=token_repo, user_repository=user_repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    token: TokenDep,
    auth_service: AuthServiceDep,
) -> User:
    payload_user = await AuthService.validate_payload(token=token)
    if payload_user.scope != TokenScope.ACCESS:
        logger.info(
            AuthErrors.INVALID_TOKEN_SCOPE.log_event,
            expected=TokenScope.ACCESS,
            received=payload_user.scope,
            user_id=str(payload_user.sub) if payload_user.sub else None,
        )
        AuthErrors.INVALID_TOKEN_SCOPE.raise_http()
    user = await auth_service.get_current_user(payload=payload_user)
    logger.debug(LogEvents.ACCESS_TOKEN_VALIDATED, user_id=str(user.id))
    return user


async def _verify_login_password(password: str, user: User) -> bool:
    return await asyncio.to_thread(
        PasswordUtils.validate_password,
        password,
        str(user.hashed_password),
    )


async def authenticate(
    auth_service: AuthServiceDep,
    form_data: UserPasswordRequestFormDep,
) -> User:
    user = await auth_service.user_repo.get_user_by_email(email=form_data.username)
    if not user or not await _verify_login_password(password=form_data.password, user=user):
        # Do not log email/password — only that credentials were rejected.
        logger.info(AuthErrors.AUTHENTICATION_FAILED.log_event, reason="invalid_credentials")
        AuthErrors.AUTHENTICATION_FAILED.raise_http()
    logger.debug(LogEvents.AUTHENTICATION_SUCCESSFUL, user_id=str(user.id))
    return user


AuthUserDep = Annotated[User, Depends(authenticate)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def validate_refresh_token(token: RefreshTokenDep) -> str:
    token_payload = await AuthService.validate_payload(token=token)
    if token_payload.scope != TokenScope.REFRESH:
        logger.info(
            AuthErrors.INVALID_TOKEN_SCOPE.log_event,
            expected=TokenScope.REFRESH,
            received=token_payload.scope,
            user_id=str(token_payload.sub) if token_payload.sub else None,
        )
        AuthErrors.INVALID_TOKEN_SCOPE.raise_http()
    return token


RefreshTokenValidatedDep = Annotated[str, Depends(validate_refresh_token)]


async def revoke_current_token(
    auth_service: AuthServiceDep,
    token: RefreshTokenDep,
) -> None:
    token_payload = await AuthService.validate_payload(token=token)
    if token_payload.scope != TokenScope.REFRESH:
        logger.info(
            AuthErrors.INVALID_TOKEN_SCOPE.log_event,
            expected=TokenScope.REFRESH,
            received=token_payload.scope,
            user_id=str(token_payload.sub) if token_payload.sub else None,
        )
        AuthErrors.INVALID_TOKEN_SCOPE.raise_http()

    token_hash = TokenCryptoUtils.hash_token(token=token)
    db_token = await auth_service.token_repo.revoke_token(user_id=token_payload.sub, token=token_hash)
    if not db_token:
        logger.info(
            AuthErrors.TOKEN_NOT_FOUND.log_event,
            user_id=str(token_payload.sub) if token_payload.sub else None,
        )
        AuthErrors.TOKEN_NOT_FOUND.raise_http()
    logger.debug(
        LogEvents.TOKEN_REVOKED,
        user_id=str(token_payload.sub) if token_payload.sub else None,
    )


LogoutTokenDep = Annotated[None, Depends(revoke_current_token)]
