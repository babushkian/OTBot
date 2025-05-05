"""Клавиатуры для фиксации нарушения."""
from aiogram.types import InlineKeyboardMarkup

from bot.enums import ViolationCategory
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.keyboards.inline_keyboards.callback_factories import ViolationCategoryFactory


async def violation_categories_kb() -> InlineKeyboardMarkup:
    """Клавиатура для выбора категории нарушений."""
    roles = tuple([{"category": line.name, "name": line.value} for line in ViolationCategory])

    return await create_keyboard(
        items=roles,
        text_key="name",
        callback_factory=ViolationCategoryFactory,
    )
