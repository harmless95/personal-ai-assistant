from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.client import ApiClientError, AssistantApiClient
from app.bot.fsm import CheckinStates
from app.bot.services import AuthRequiredError, call_with_refresh, wait_for_artifact
from app.bot.sessions import SessionStore
from app.bot.ui import format_artifact, format_question
from app.config import settings

router = Router(name="checkin_questions")


@router.message(StateFilter(CheckinStates.answering), F.text)
async def on_question_answer(
    message: Message,
    state: FSMContext,
    api: AssistantApiClient,
    sessions: SessionStore,
) -> None:
    if message.from_user is None:
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer("Нужен непустой ответ.")
        return

    data = await state.get_data()
    questions: list[dict[str, Any]] = list(data.get("questions") or [])
    answers: list[dict[str, str]] = list(data.get("answers") or [])
    index = int(data.get("question_index") or 0)
    checkin_id = data.get("checkin_id")

    if not questions or checkin_id is None:
        await state.clear()
        await message.answer("Сессия check-in потеряна. Начни заново: /checkin")
        return

    question = questions[index]
    answers.append(
        {
            "question_id": str(question["question_id"]),
            "answer_text": text,
        }
    )
    index += 1

    if index < len(questions):
        await state.update_data(answers=answers, question_index=index)
        await message.answer(format_question(index + 1, len(questions), questions[index]))
        return

    await message.answer("Сохраняю ответы и жду итог дня…")
    try:

        async def _answer(access_token: str) -> dict[str, Any]:
            return await api.answer_checkin(
                access_token=access_token,
                checkin_id=str(checkin_id),
                answers=answers,
            )

        await call_with_refresh(
            api=api,
            store=sessions,
            telegram_user_id=message.from_user.id,
            action=_answer,
        )
        artifact = await wait_for_artifact(
            api=api,
            store=sessions,
            telegram_user_id=message.from_user.id,
            checkin_id=str(checkin_id),
            poll_interval_seconds=settings.telegram.artifact_poll_interval_seconds,
            poll_timeout_seconds=settings.telegram.artifact_poll_timeout_seconds,
        )
    except AuthRequiredError:
        await state.clear()
        await message.answer("Сначала войди: /login")
        return
    except (ApiClientError, TimeoutError) as error:
        await state.clear()
        await message.answer(f"Не удалось получить итог: {error}")
        return

    await state.clear()
    await message.answer(format_artifact(artifact))


async def start_questions(
    *,
    message: Message,
    state: FSMContext,
    api: AssistantApiClient,
    sessions: SessionStore,
    telegram_user_id: int,
    checkin_state: dict[str, int],
) -> None:
    try:

        async def _ask(access_token: str) -> dict[str, Any]:
            return await api.ask_checkin(access_token=access_token, state=checkin_state)

        ask_payload = await call_with_refresh(
            api=api,
            store=sessions,
            telegram_user_id=telegram_user_id,
            action=_ask,
        )
    except AuthRequiredError:
        await state.clear()
        await message.answer("Сначала войди: /login")
        return
    except ApiClientError as error:
        await state.clear()
        await message.answer(f"Не удалось начать check-in: {error}")
        return

    questions = ask_payload.get("selected_questions") or []
    checkin_id = ask_payload.get("checkin_id")
    if not questions or checkin_id is None:
        await state.clear()
        await message.answer("API не вернул вопросы. Попробуй позже.")
        return

    await state.set_state(CheckinStates.answering)
    await state.update_data(
        checkin_id=str(checkin_id),
        questions=questions,
        answers=[],
        question_index=0,
    )
    await message.answer(format_question(1, len(questions), questions[0]))
