"""Функция для создания inline клавиатуры."""
from typing import Any
from collections.abc import Callable

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.common_keyboards import CancelCallbackFactory


async def create_keyboard(items: tuple,
                          text_key: str,
                          callback_factory: Callable[..., Any],
                          ) -> InlineKeyboardMarkup:
    """Создание inline клавиатуры."""
    builder = InlineKeyboardBuilder()

    for item in items:
        builder.button(
            text=item[text_key],
            callback_data=callback_factory(**item),
        )

    cancel_callback_data = CancelCallbackFactory(action="cancel")
    builder.button(
        text="Отмена",
        callback_data=cancel_callback_data,
    )
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)
