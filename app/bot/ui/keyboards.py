from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def scale_keyboard(prefix: str, *, min_value: int = 1, max_value: int = 5) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=str(value), callback_data=f"{prefix}:{value}")
        for value in range(min_value, max_value + 1)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def yes_no_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Нет (0)", callback_data=f"{prefix}:0"),
                InlineKeyboardButton(text="Да (1)", callback_data=f"{prefix}:1"),
            ]
        ]
    )
