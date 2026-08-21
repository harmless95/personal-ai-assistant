from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

import jwt
from pydantic import BaseModel, ConfigDict

JWT_SUB_KEY: str = "sub"
JWT_EXP_KEY: str = "exp"
DEFAULT_JWT_ALGORITHM: str = "HS256"
JWT_SCOPE_KEY: str = "scope"


class TokenScope(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    sub: UUID
    exp: datetime
    scope: TokenScope

    model_config = ConfigDict(from_attributes=True)

    def to_jwt_dict(self) -> dict[str, Any]:
        return {
            JWT_SUB_KEY: str(self.sub),
            JWT_EXP_KEY: int(self.exp.timestamp()),
            JWT_SCOPE_KEY: self.scope.value,
        }

    @classmethod
    def from_jwt(cls, token: str, secret: str, algorithm: str = DEFAULT_JWT_ALGORITHM) -> "TokenPayload":
        raw = jwt.decode(token, secret, algorithms=[algorithm])
        raw[JWT_EXP_KEY] = datetime.fromtimestamp(raw[JWT_EXP_KEY], tz=timezone.utc)
        return cls(**raw)
