from aiogram import F, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.client import ApiClientError, AssistantApiClient
from app.bot.fsm import AuthStates
from app.bot.sessions import SessionStore, UserSession

router = Router(name="auth")


@router.message(Command("login"))
async def cmd_login(
    message: Message,
    state: FSMContext,
    command: CommandObject,
    api: AssistantApiClient,
    sessions: SessionStore,
) -> None:
    args = (command.args or "").split()
    if len(args) >= 2:
        email, password = args[0], " ".join(args[1:])
        await _login_and_reply(
            message=message,
            state=state,
            api=api,
            sessions=sessions,
            email=email,
            password=password,
        )
        return

    await state.set_state(AuthStates.waiting_email)
    await message.answer("Введи email:")


@router.message(StateFilter(AuthStates.waiting_email), F.text)
async def login_email(message: Message, state: FSMContext) -> None:
    email = (message.text or "").strip()
    if "@" not in email:
        await message.answer("Похоже, это не email. Попробуй ещё раз:")
        return
    await state.update_data(login_email=email)
    await state.set_state(AuthStates.waiting_password)
    await message.answer("Введи пароль:")


@router.message(StateFilter(AuthStates.waiting_password), F.text)
async def login_password(
    message: Message,
    state: FSMContext,
    api: AssistantApiClient,
    sessions: SessionStore,
) -> None:
    data = await state.get_data()
    email = str(data.get("login_email", ""))
    password = message.text or ""
    await _login_and_reply(
        message=message,
        state=state,
        api=api,
        sessions=sessions,
        email=email,
        password=password,
    )


@router.message(Command("logout"))
async def cmd_logout(message: Message, state: FSMContext, sessions: SessionStore) -> None:
    if message.from_user is None:
        return
    sessions.clear(message.from_user.id)
    await state.clear()
    await message.answer("Вышел. Чтобы снова пользоваться ботом: /login")


async def _login_and_reply(
    *,
    message: Message,
    state: FSMContext,
    api: AssistantApiClient,
    sessions: SessionStore,
    email: str,
    password: str,
) -> None:
    if message.from_user is None:
        return
    try:
        tokens = await api.login(email=email, password=password)
    except ApiClientError as error:
        await message.answer(f"Не удалось войти: {error}")
        await state.clear()
        return

    sessions.set(
        message.from_user.id,
        UserSession(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            email=email,
        ),
    )
    await state.clear()
    await message.answer(f"Готово, ты вошёл как {email}.\nДальше: /checkin")
