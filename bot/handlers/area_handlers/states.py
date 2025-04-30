"""Состояния для добавления места нарушения."""
from aiogram.fsm.state import State, StatesGroup


class AreaAddOrUpdateStates(StatesGroup):
    """Состояния для добавления/обновления места нарушения."""

    start = State()
    enter_area_name = State()
    enter_area_description = State()
    enter_responsible = State()
    enter_responsible_text = State()
    update_responsible = State()
    update_field = State()
    completed = State()
