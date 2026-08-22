from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router(name="start")


@router.message(CommandStart())
@router.message(Command("help"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Personal AI Assistant — daily check-in бот.\n\n"
        "Команды:\n"
        "/login — войти (email и пароль аккаунта API)\n"
        "/logout — выйти\n"
        "/checkin — пройти check-in дня\n"
        "/history — последние check-in\n"
        "/cancel — отменить текущий диалог\n\n"
        "1) Зарегистрируйся через API/Swagger\n"
        "2) /login\n"
        "3) /checkin"
    )
