"""Состояния заполнения данных для подтверждения пользователя."""

from aiogram.fsm.state import State, StatesGroup


class ApproveUserStates(StatesGroup):
    """Состояния заполнения данных для подтверждения пользователя."""

    started = State()
    name_enter = State()
    role_enter = State()
    completed = State()
