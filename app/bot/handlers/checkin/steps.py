from __future__ import annotations

from typing import Any

from app.bot.fsm import CheckinStates
from app.bot.ui import scale_keyboard, yes_no_keyboard

STATE_STEPS: list[tuple[Any, str, Any, str]] = [
    (CheckinStates.stress_level, "Оцени стресс сегодня (1–5):", scale_keyboard("stress"), "stress_level"),
    (CheckinStates.energy_level, "Оцени энергию (1–5):", scale_keyboard("energy"), "energy_level"),
    (CheckinStates.plan_done, "Насколько выполнен план дня (1–5):", scale_keyboard("plan"), "plan_done"),
    (CheckinStates.blocker_present, "Есть ли блокер сегодня?", yes_no_keyboard("blocker"), "blocker_present"),
    (
        CheckinStates.learning_done,
        "Насколько получилось поучиться (1–5):",
        scale_keyboard("learning"),
        "learning_done",
    ),
]

PREFIX_TO_FIELD = {
    "stress": "stress_level",
    "energy": "energy_level",
    "plan": "plan_done",
    "blocker": "blocker_present",
    "learning": "learning_done",
}


def next_step_index(current_field: str) -> int | None:
    order = [step[3] for step in STATE_STEPS]
    try:
        index = order.index(current_field)
    except ValueError:
        return None
    next_index = index + 1
    if next_index >= len(STATE_STEPS):
        return None
    return next_index
