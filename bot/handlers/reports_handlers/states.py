"""Состояния для работы с отчетами."""

from aiogram.fsm.state import State, StatesGroup


class ReportStates(StatesGroup):
    """Состояния для работы с отчетами."""

    by_id = State()
    active = State()
    sum = State()
