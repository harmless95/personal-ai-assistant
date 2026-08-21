from dataclasses import dataclass
from typing import NoReturn

from fastapi import HTTPException, status


@dataclass(frozen=True)
class AuthError:
    id: str
    detail: str
    status_code: int = status.HTTP_400_BAD_REQUEST

    @property
    def log_event(self) -> str:
        return self.id

    def raise_http(self) -> NoReturn:
        raise HTTPException(
            status_code=self.status_code,
            detail={"id": self.id, "message": self.detail},
        )


class AuthErrors:
    INVALID_TOKEN_SCOPE = AuthError(
        id="invalid_token_scope",
        detail="Invalid token scope",
        status_code=status.HTTP_403_FORBIDDEN,
    )
    AUTHENTICATION_FAILED = AuthError(
        id="authentication_failed",
        detail="Authentication failed",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )
    TOKEN_NOT_FOUND = AuthError(
        id="token_not_found",
        detail="Token not found or already revoked",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )
    EMAIL_ALREADY_TAKEN = AuthError(
        id="email_already_taken",
        detail="Email is already taken",
        status_code=status.HTTP_409_CONFLICT,
    )
    TOKEN_MISSING_SUBJECT = AuthError(
        id="token_missing_subject",
        detail="Invalid token: missing subject",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )
    USER_NOT_FOUND = AuthError(
        id="user_not_found",
        detail="User not found",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )
    TOKEN_INVALID = AuthError(
        id="token_invalid",
        detail="Invalid token",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )
    TOKEN_EXPIRED = AuthError(
        id="token_expired",
        detail="Token has expired",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )
    INVALID_EMAIL = AuthError(
        id="invalid_email",
        detail="Invalid email address",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    PASSWORD_TOO_SHORT = AuthError(
        id="password_too_short",
        detail="Password is too short",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    PASSWORD_TOO_LONG = AuthError(
        id="password_too_long",
        detail="Password is too long",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    PASSWORD_MISSING_SPECIAL = AuthError(
        id="password_missing_special_character",
        detail="Password must contain at least one special character",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    PASSWORD_MISSING_UPPERCASE = AuthError(
        id="password_missing_uppercase",
        detail="Password must contain at least one uppercase letter",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    PASSWORD_MISSING_DIGIT = AuthError(
        id="password_missing_digit",
        detail="Password must contain at least one digit",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    INVALID_NAME = AuthError(
        id="invalid_name",
        detail="Name must be between 2 and 128 characters",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    INVALID_SURNAME = AuthError(
        id="invalid_surname",
        detail="Surname must be between 2 and 128 characters",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
    USER_LIMIT_REACHED = AuthError(
        id="user_limit_reached",
        detail="limit reached",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )


class LogEvents:
    ACCESS_TOKEN_VALIDATED = "access_token_validated"
    AUTHENTICATION_SUCCESSFUL = "authentication_successful"
    TOKEN_REVOKED = "token_successfully_revoked"
    TOKENS_CREATION_STARTED = "tokens_creation_started"
    TOKENS_CREATED_SUCCESSFULLY = "tokens_created_successfully"
    TOKEN_REFRESH_SUCCESSFUL = "token_refresh_successful"
    USER_REGISTERED = "user_successfully_registered"
    USER_LIMIT_REACHED = "user_registration_limit_reached"
