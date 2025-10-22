"""Клавиатуры общих команд."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters.callback_data import CallbackData


def generate_share_contact_keyboard() -> ReplyKeyboardMarkup:
    """Генерирует клавиатуру с кнопками "Поделиться контактом" и "Отмена"."""
    share_contact_button = KeyboardButton(text="📱 Поделиться контактом", request_contact=True)
    cancel_button = KeyboardButton(text="❌ Отмена")

    return ReplyKeyboardMarkup(keyboard=[[share_contact_button], [cancel_button]],
                               resize_keyboard=True,
                               one_time_keyboard=True)


def generate_yes_no_keyboard() -> ReplyKeyboardMarkup:
    """Генерирует клавиатуру с кнопками "Да" и "Нет"."""
    yes_button = KeyboardButton(text="✅ Да")
    no_button = KeyboardButton(text="❌ Нет")

    return ReplyKeyboardMarkup(
        keyboard=[[yes_button], [no_button]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_cancel_button() -> ReplyKeyboardMarkup:
    """Генерирует клавиатуру с кнопками "Поделиться контактом" и "Отмена"."""
    cancel_button = KeyboardButton(text="❌ Отмена")

    return ReplyKeyboardMarkup(keyboard=[[cancel_button]],
                               resize_keyboard=True,
                               one_time_keyboard=True)


class CancelCallbackFactory(CallbackData, prefix="cancel"):
    """Фабрика для кнопки "Отмена"."""

    action: str
