from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api.auth.endpoints.auth import router as auth_router
from app.api.daily_checkin.endpoints.daily_checkin import router as daily_router
from app.api.utils.endpoints.health_check import router
from app.config import settings
from app.db.session import dispose
from app.tasks.broker_taskiq import broker


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    try:
        if not broker.is_worker_process:
            await broker.startup()
        yield
    finally:
        await dispose()
        if not broker.is_worker_process:
            await broker.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(router=router, prefix=settings.api_prefix_v1)
app.include_router(router=auth_router, prefix=settings.api_prefix_v1)
app.include_router(router=daily_router, prefix=settings.api_prefix_v1)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host.host,
        port=settings.host.port,
    )
