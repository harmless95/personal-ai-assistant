import re
from datetime import datetime
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, field_validator

from app.api.auth.errors import AuthErrors

PASSWORD_MIN_LENGTH: int = 8
PASSWORD_MAX_LENGTH: int = 72
NAME_MIN_LENGTH: int = 2
NAME_MAX_LENGTH: int = 128


class UserBase(BaseModel):
    email: str
    password: str
    name: str
    surname: str

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, value: str) -> str:
        try:
            return validate_email(value, check_deliverability=False).normalized
        except EmailNotValidError:
            AuthErrors.INVALID_EMAIL.raise_http()

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not NAME_MIN_LENGTH <= len(value) <= NAME_MAX_LENGTH:
            AuthErrors.INVALID_NAME.raise_http()
        return value

    @field_validator("surname")
    @classmethod
    def validate_surname(cls, value: str) -> str:
        if not NAME_MIN_LENGTH <= len(value) <= NAME_MAX_LENGTH:
            AuthErrors.INVALID_SURNAME.raise_http()
        return value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < PASSWORD_MIN_LENGTH:
            AuthErrors.PASSWORD_TOO_SHORT.raise_http()

        if len(value) > PASSWORD_MAX_LENGTH:
            AuthErrors.PASSWORD_TOO_LONG.raise_http()

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            AuthErrors.PASSWORD_MISSING_SPECIAL.raise_http()

        if not re.search(r"[A-Z]", value):
            AuthErrors.PASSWORD_MISSING_UPPERCASE.raise_http()

        if not re.search(r"[0-9]", value):
            AuthErrors.PASSWORD_MISSING_DIGIT.raise_http()

        return value


class RegisterRequest(UserBase):
    pass


class RegisterResponse(BaseModel):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    surname: str

    model_config = ConfigDict(from_attributes=True)


class StatusResponse(BaseModel):
    detail: str
