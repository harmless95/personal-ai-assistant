import uvicorn
from fastapi import FastAPI

from app.api.daily_checkin.endpoints.daily_checkin import router as daily_router
from app.api.utils.endpoints.health_check import router
from app.config import settings

app = FastAPI()

app.include_router(router=router, prefix=settings.api_prefix_v1)
app.include_router(router=daily_router, prefix=settings.api_prefix_v1)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host.host,
        port=settings.host.port,
    )
