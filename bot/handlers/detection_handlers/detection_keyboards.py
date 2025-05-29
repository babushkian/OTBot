"""Клавиатуры для фиксации нарушения."""
import asyncio

from aiogram.types import InlineKeyboardMarkup

from bot.keyboards.keyboard_utils import read_categories_json_file
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.keyboards.inline_keyboards.callback_factories import ViolationCategoryFactory


async def violation_categories_first_kb() -> InlineKeyboardMarkup:
    """Клавиатуры для выбора категории нарушений."""
    buttons_json = read_categories_json_file()
    first_keyboard_data = tuple([{"name": values["button_name"], "category": cell_id}
                                 for cell_id, values in buttons_json[0].items()])

    return await create_keyboard(items=first_keyboard_data, text_key="name",
                                 callback_factory=ViolationCategoryFactory)


async def create_violation_keyboard_by_cell_id(cell_id: str) -> InlineKeyboardMarkup | None:
    """Создание клавиатуры для фиксации нарушения по id."""
    buttons_json = read_categories_json_file()
    next_button = None

    for button in buttons_json:
        next_button = button.get(cell_id)
        if next_button is not None:
            break

    if next_button is None:
        return None

    next_layer_data = tuple([{"name": button_cell_id, "category": button_name}
                             for button_name, button_cell_id
                             in next_button["button_values"].items()])

    return await create_keyboard(items=next_layer_data, text_key="name",
                                 callback_factory=ViolationCategoryFactory)


async def get_violation_category_by_cell_id(cell_id: str) -> str | None:
    """Получение категории нарушения по id."""
    buttons_json = read_categories_json_file()
    category_name = None
    for buttons in buttons_json:
        for button_data in buttons.values():
            category_name = button_data["button_values"].get(cell_id)
            if category_name is not None:
                break
        if category_name is not None:
            break
    return category_name


if __name__ == "__main__":
    # result = asyncio.run(create_violation_keyboard_by_cell_id("B4"))
    # result = asyncio.run(violation_categories_first_kb())
    result = asyncio.run(get_violation_category_by_cell_id("B4"))
