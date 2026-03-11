"""Состояния для обнаружения нарушений."""

from aiogram.fsm.state import State, StatesGroup

class ViolationCheckStates(StatesGroup):
    """Состояния нарушений."""

    start = State()

    review = State()
    # состояния для легкой версии
    lstart = State()
    lreview = State()

    activate = State()
    reject = State()

# class LightViolationCheckStates(StatesGroup):
#     """Состояния нарушений."""
#
#     start = State()
#     review = State()
#
#     activate = State()
#     reject = State()
