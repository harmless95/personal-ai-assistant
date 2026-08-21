import asyncio
from logging import getLogger
from typing import Annotated

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

logger = getLogger(__name__)

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
            "%s expected=%s received=%s user_id=%s",
            AuthErrors.INVALID_TOKEN_SCOPE.log_event,
            TokenScope.ACCESS,
            payload_user.scope,
            payload_user.sub,
        )
        AuthErrors.INVALID_TOKEN_SCOPE.raise_http()
    user = await auth_service.get_current_user(payload=payload_user)
    logger.debug("%s user_id=%s", LogEvents.ACCESS_TOKEN_VALIDATED, user.id)
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
        logger.info("%s reason=invalid_credentials", AuthErrors.AUTHENTICATION_FAILED.log_event)
        AuthErrors.AUTHENTICATION_FAILED.raise_http()
    logger.debug("%s user_id=%s", LogEvents.AUTHENTICATION_SUCCESSFUL, user.id)
    return user


AuthUserDep = Annotated[User, Depends(authenticate)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def validate_refresh_token(token: RefreshTokenDep) -> str:
    token_payload = await AuthService.validate_payload(token=token)
    if token_payload.scope != TokenScope.REFRESH:
        logger.info(
            "%s expected=%s received=%s user_id=%s",
            AuthErrors.INVALID_TOKEN_SCOPE.log_event,
            TokenScope.REFRESH,
            token_payload.scope,
            token_payload.sub,
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
            "%s expected=%s received=%s user_id=%s",
            AuthErrors.INVALID_TOKEN_SCOPE.log_event,
            TokenScope.REFRESH,
            token_payload.scope,
            token_payload.sub,
        )
        AuthErrors.INVALID_TOKEN_SCOPE.raise_http()

    token_hash = TokenCryptoUtils.hash_token(token=token)
    db_token = await auth_service.token_repo.revoke_token(user_id=token_payload.sub, token=token_hash)
    if not db_token:
        logger.info("%s user_id=%s", AuthErrors.TOKEN_NOT_FOUND.log_event, token_payload.sub)
        AuthErrors.TOKEN_NOT_FOUND.raise_http()
    logger.debug("%s user_id=%s", LogEvents.TOKEN_REVOKED, token_payload.sub)


LogoutTokenDep = Annotated[None, Depends(revoke_current_token)]
