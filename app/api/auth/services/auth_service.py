import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
import structlog
from jwt import InvalidTokenError

from app.api.auth.data.token_repository import TokenRepository
from app.api.auth.data.user_repository import UserRepository
from app.api.auth.errors import AuthErrors, LogEvents
from app.api.auth.models.token import TokenPayload, TokenResponse, TokenScope
from app.api.auth.models.user import RegisterRequest, RegisterResponse
from app.api.auth.utils.password import PasswordUtils
from app.api.auth.utils.token import TokenCryptoUtils
from app.config import Environment, settings
from app.db import User

logger = structlog.get_logger(__name__)


class AuthService:
    def __init__(
        self,
        token_repository: TokenRepository,
        user_repository: UserRepository,
    ):
        self.token_repo = token_repository
        self.user_repo = user_repository

    async def get_tokens(self, user_id: UUID) -> TokenResponse:
        logger.debug(LogEvents.TOKENS_CREATION_STARTED, user_id=str(user_id))
        access_token = await AuthService._create_access_token(user_id=user_id)
        refresh_token = await self._create_refresh_token(user_id=user_id)
        logger.debug(LogEvents.TOKENS_CREATED_SUCCESSFULLY, user_id=str(user_id))
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh_access(self, refresh_token: str) -> TokenResponse:
        token_payload = await AuthService.validate_payload(token=refresh_token)
        if token_payload.scope != TokenScope.REFRESH:
            logger.info(
                AuthErrors.INVALID_TOKEN_SCOPE.log_event,
                user_id=str(token_payload.sub) if token_payload.sub else None,
                expected=TokenScope.REFRESH,
                received=token_payload.scope,
            )
            AuthErrors.INVALID_TOKEN_SCOPE.raise_http()
        token_hash = TokenCryptoUtils.hash_token(token=refresh_token)
        db_token = await self.token_repo.revoke_token(user_id=token_payload.sub, token=token_hash)
        if not db_token:
            logger.info(
                AuthErrors.TOKEN_NOT_FOUND.log_event,
                user_id=str(token_payload.sub) if token_payload.sub else None,
            )
            AuthErrors.TOKEN_NOT_FOUND.raise_http()
        logger.debug(
            LogEvents.TOKEN_REFRESH_SUCCESSFUL,
            user_id=str(token_payload.sub) if token_payload.sub else None,
        )
        return await self.get_tokens(user_id=token_payload.sub)

    async def _create_refresh_token(self, user_id: UUID) -> str:
        now = datetime.now(timezone.utc)
        expire_at = now + timedelta(days=settings.auth_jwt.refresh_token_expire_days)
        jwt_payload = TokenPayload(sub=user_id, exp=expire_at, scope=TokenScope.REFRESH)
        refresh_token = await asyncio.to_thread(
            jwt.encode,
            payload=jwt_payload.to_jwt_dict(),
            key=settings.auth_jwt.secret_key.get_secret_value(),
            algorithm=settings.auth_jwt.algorithm_jwt,
        )
        token_hash = TokenCryptoUtils.hash_token(token=refresh_token)
        await self.token_repo.create_refresh_token(
            user_id=user_id,
            token=token_hash,
        )
        return refresh_token

    async def register_new_user(self, register_request: RegisterRequest) -> RegisterResponse:
        if settings.environment == Environment.STAGING:
            user_count = await self.user_repo.count_users()
            if user_count >= settings.staging.max_users:
                logger.info(
                    AuthErrors.USER_LIMIT_REACHED.log_event,
                    user_count=user_count,
                    max_users=settings.staging.max_users,
                )
                AuthErrors.USER_LIMIT_REACHED.raise_http()

        existing_user = await self.user_repo.get_user_by_email(email=str(register_request.email))
        if existing_user:
            # Do not log email — only the event.
            logger.info(AuthErrors.EMAIL_ALREADY_TAKEN.log_event)
            AuthErrors.EMAIL_ALREADY_TAKEN.raise_http()

        hashed_password = await asyncio.to_thread(
            PasswordUtils.hash_password,
            password=register_request.password,
        )
        new_user = await self.user_repo.create_user(
            email=str(register_request.email),
            hashed_password=hashed_password,
            name=register_request.name,
            surname=register_request.surname,
        )
        logger.debug(LogEvents.USER_REGISTERED, user_id=str(new_user.id))
        return RegisterResponse.model_validate(new_user)

    async def get_current_user(
        self,
        payload: TokenPayload,
    ) -> User:
        if not payload.sub:
            logger.info(AuthErrors.TOKEN_MISSING_SUBJECT.log_event)
            AuthErrors.TOKEN_MISSING_SUBJECT.raise_http()
        user = await self.user_repo.get_user_by_id(id=payload.sub)
        if not user:
            logger.info(AuthErrors.USER_NOT_FOUND.log_event, user_id=str(payload.sub))
            AuthErrors.USER_NOT_FOUND.raise_http()
        return user

    @staticmethod
    async def _create_access_token(user_id: UUID) -> str:
        now = datetime.now(timezone.utc)
        expire_at = now + timedelta(minutes=settings.auth_jwt.access_token_expire_minutes)
        jwt_payload = TokenPayload(sub=user_id, exp=expire_at, scope=TokenScope.ACCESS)
        return await asyncio.to_thread(
            jwt.encode,
            payload=jwt_payload.to_jwt_dict(),
            key=settings.auth_jwt.secret_key.get_secret_value(),
            algorithm=settings.auth_jwt.algorithm_jwt,
        )

    @staticmethod
    async def validate_payload(token: str) -> TokenPayload:
        try:
            return await asyncio.to_thread(
                TokenPayload.from_jwt,
                token=token,
                secret=settings.auth_jwt.secret_key.get_secret_value(),
                algorithm=settings.auth_jwt.algorithm_jwt,
            )
        except InvalidTokenError as e:
            is_expired = "expired" in str(e).lower()
            if is_expired:
                error = AuthErrors.TOKEN_EXPIRED
                logger.info(error.log_event, error_type="expired")
            else:
                error = AuthErrors.TOKEN_INVALID
                logger.info(error.log_event, error_type="invalid")
            error.raise_http()
