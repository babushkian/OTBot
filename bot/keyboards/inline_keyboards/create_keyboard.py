"""Функция для создания inline клавиатуры."""
from typing import Any
from collections.abc import Callable

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.common_keyboards import CancelCallbackFactory
from bot.keyboards.inline_keyboards.callback_factories import MultiSelectCallbackFactory


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


async def create_multi_select_keyboard(items: list[dict]) -> InlineKeyboardMarkup:
    """Создает inline-клавиатуру с возможностью множественного выбора."""
    selected_ids = set()

    builder = InlineKeyboardBuilder()

    for item in items:
        item_id = item["id"]
        text = item["text"]
        is_selected = item_id in selected_ids

        button_text = f"{'✅' if is_selected else '❌'} {text}"
        builder.button(
            text=button_text,
            callback_data=MultiSelectCallbackFactory(id=item_id,
                                                     selected=is_selected,
                                                     action="select"),
        )

        # Добавляем кнопку "ОК"
    builder.button(
        text="✅ ОК",
        callback_data=MultiSelectCallbackFactory(action="ok"),
    )

    builder.adjust(1)
    return builder.as_markup()
