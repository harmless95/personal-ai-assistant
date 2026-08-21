from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.__session = session

    async def create_user(self, email: str, hashed_password: str, name: str, surname: str) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            name=name,
            surname=surname,
        )
        self.__session.add(user)
        await self.__session.flush()
        await self.__session.refresh(user)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        user: User | None = await self.__session.scalar(select(User).where(User.email == email.lower()))
        return user

    async def get_user_by_id(self, id: UUID) -> User | None:
        user: User | None = await self.__session.scalar(select(User).where(User.id == id))
        return user

    async def count_users(self) -> int:
        count: int | None = await self.__session.scalar(select(func.count()).select_from(User))
        return count or 0
