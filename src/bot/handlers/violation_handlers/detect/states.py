"""Состояния для обнаружения нарушений."""

from aiogram.fsm.state import State, StatesGroup


class DetectionStates(StatesGroup):
    """Состояния для обнаружения нарушений."""

    start = State()
    send_photo = State()
    send_media_group = State()
    enter_area = State()
    next_layer_select_category = State()

    first_layer_select_category = State()
    second_layer_select_category = State()
    third_layer_select_category = State()  # для увеличения глубины выбора категории

    select_category = State()
    select_actions_needed = State()
    completed = State()
