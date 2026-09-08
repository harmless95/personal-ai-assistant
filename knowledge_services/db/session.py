from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from knowledge_services.config import settings

async_engine = create_async_engine(
    url=str(settings.db.url.get_secret_value()),  # type: ignore[attr-defined]
    echo=settings.db.echo,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
    pool_pre_ping=settings.db.pool_pre_ping,
    pool_recycle=settings.db.pool_recycle,
    pool_timeout=settings.db.pool_timeout,
    echo_pool=settings.db.echo_pool,
)
SessionFactory = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def dispose() -> None:
    await async_engine.dispose()


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> AsyncIterator[AsyncSession]:
    factory = session_factory or SessionFactory
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def session_getter() -> AsyncGenerator[AsyncSession, None]:
    async with session_scope() as session:
        yield session
