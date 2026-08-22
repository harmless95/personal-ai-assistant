from aiogram import Router

from app.bot.handlers.checkin import history, questions, wizard

router = Router(name="checkin")
router.include_router(wizard.router)
router.include_router(questions.router)
router.include_router(history.router)
