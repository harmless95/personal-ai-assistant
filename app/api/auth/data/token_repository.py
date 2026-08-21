from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.refresh_token import RefreshToken


class TokenRepository:
    def __init__(self, session: AsyncSession):
        self.__session = session

    async def create_refresh_token(self, user_id: UUID, token: str) -> RefreshToken:
        refresh_token = RefreshToken(user_id=user_id, token=token)
        self.__session.add(refresh_token)
        await self.__session.flush()
        await self.__session.refresh(refresh_token)
        return refresh_token

    async def revoke_token(
        self,
        user_id: UUID,
        token: str,
    ) -> RefreshToken | None:
        stmt = select(RefreshToken).where(
            RefreshToken.token == token,
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked.is_(False),
        )
        result = await self.__session.execute(stmt)
        db_token = result.scalar_one_or_none()
        if db_token:
            db_token.is_revoked = True
            await self.__session.flush()
        return db_token
