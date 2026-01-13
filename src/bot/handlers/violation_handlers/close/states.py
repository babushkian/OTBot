"""Состояния управления нарушениями."""

from aiogram.fsm.state import State, StatesGroup


class ViolationCloseStates(StatesGroup):
    """Состояния нарушений."""

    start = State()
    review = State()
    close = State()
