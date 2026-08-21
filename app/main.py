from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi_structlog import setup_logger
from fastapi_structlog.middleware import AccessLogMiddleware, CurrentScopeSetMiddleware, StructlogMiddleware
from starlette.middleware import Middleware

from app.api.auth.endpoints.auth import router as auth_router
from app.api.daily_checkin.endpoints.daily_checkin import router as daily_router
from app.api.utils.endpoints.health_check import router
from app.config import Environment, settings
from app.db.session import dispose
from app.tasks.broker_taskiq import broker

setup_logger(settings.log)

logger = structlog.get_logger(__name__)
logger.info("application_start")


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


docs_disabled = settings.environment != Environment.DEVELOPMENT

app = FastAPI(
    lifespan=lifespan,
    docs_url=None if docs_disabled else "/docs",
    redoc_url=None if docs_disabled else "/redoc",
    openapi_url=None if docs_disabled else "/openapi.json",
    middleware=[
        Middleware(CurrentScopeSetMiddleware),
        Middleware(CorrelationIdMiddleware),
        Middleware(StructlogMiddleware),
        Middleware(AccessLogMiddleware),
    ],
)

app.include_router(router=router, prefix=settings.api_prefix_v1)
app.include_router(router=auth_router, prefix=settings.api_prefix_v1)
app.include_router(router=daily_router, prefix=settings.api_prefix_v1)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host.host,
        port=settings.host.port,
        access_log=False,
    )
