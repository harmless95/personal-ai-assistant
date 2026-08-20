from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

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


async def session_getter() -> AsyncGenerator[AsyncSession, None]:
    session = SessionFactory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
