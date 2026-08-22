from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.client import AssistantApiClient
from app.bot.fsm import CheckinStates
from app.bot.handlers.checkin.questions import start_questions
from app.bot.handlers.checkin.steps import PREFIX_TO_FIELD, STATE_STEPS, next_step_index
from app.bot.sessions import SessionStore

router = Router(name="checkin_wizard")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Диалог сброшен.")


@router.message(Command("checkin"))
async def cmd_checkin(message: Message, state: FSMContext, sessions: SessionStore) -> None:
    if message.from_user is None:
        return
    if sessions.get(message.from_user.id) is None:
        await message.answer("Сначала войди: /login")
        return

    await state.clear()
    await state.set_state(CheckinStates.stress_level)
    await state.update_data(checkin_state={})
    _, prompt, keyboard, _ = STATE_STEPS[0]
    await message.answer(prompt, reply_markup=keyboard)


@router.callback_query(F.data.startswith("stress:"))
@router.callback_query(F.data.startswith("energy:"))
@router.callback_query(F.data.startswith("plan:"))
@router.callback_query(F.data.startswith("blocker:"))
@router.callback_query(F.data.startswith("learning:"))
async def on_state_value(
    callback: CallbackQuery,
    state: FSMContext,
    api: AssistantApiClient,
    sessions: SessionStore,
) -> None:
    if callback.from_user is None or callback.data is None or callback.message is None:
        return

    prefix, raw_value = callback.data.split(":", maxsplit=1)
    field = PREFIX_TO_FIELD[prefix]
    value = int(raw_value)

    data = await state.get_data()
    checkin_state: dict[str, int] = dict(data.get("checkin_state") or {})
    checkin_state[field] = value
    await state.update_data(checkin_state=checkin_state)
    await callback.answer()

    step = next_step_index(field)
    if step is None:
        if not isinstance(callback.message, Message):
            return
        await callback.message.answer("Собираю вопросы…")
        await start_questions(
            message=callback.message,
            state=state,
            api=api,
            sessions=sessions,
            telegram_user_id=callback.from_user.id,
            checkin_state=checkin_state,
        )
        return

    if not isinstance(callback.message, Message):
        return
    fsm_state, prompt, keyboard, _ = STATE_STEPS[step]
    await state.set_state(fsm_state)
    await callback.message.answer(prompt, reply_markup=keyboard)
