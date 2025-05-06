"""Состояния для обнаружения нарушений."""
from aiogram.fsm.state import State, StatesGroup


class DetectionStates(StatesGroup):
    """Состояния для обнаружения нарушений."""

    start = State()
    send_photo = State()
    enter_area = State()
    select_category = State()
    select_actions_needed = State()
    completed = State()


class ViolationStates(StatesGroup):
    """Состояния нарушений."""

    start = State()
    review = State()

    activate = State()
    reject = State()
