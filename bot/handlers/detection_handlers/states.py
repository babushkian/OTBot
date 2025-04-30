"""Состояния для обнаружения нарушений."""
from aiogram.fsm.state import State, StatesGroup


class DetectionStates(StatesGroup):
    """Состояния для обнаружения нарушений."""

    start = State()
    send_photo = State()
    enter_area = State()
    enter_description = State()
    select_category = State()
    select_actions_needed = State()
    complete = State()

