from aiogram import Router

from app.bot.handlers import auth, start
from app.bot.handlers.checkin import router as checkin_router


def build_root_router() -> Router:
    root = Router(name="bot")
    root.include_router(start.router)
    root.include_router(auth.router)
    root.include_router(checkin_router)
    return root
