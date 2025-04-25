"""Клавиатуры для одобрения пользователей."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def generate_share_contact_keyboard() -> ReplyKeyboardMarkup:
    """Генерирует клавиатуру с кнопками "Поделиться контактом" и "Отмена"."""
    share_contact_button = KeyboardButton(text="📱 Поделиться контактом", request_contact=True)
    cancel_button = KeyboardButton(text="❌ Отмена")

    return ReplyKeyboardMarkup(keyboard=[[share_contact_button], [cancel_button]],
                               resize_keyboard=True,
                               one_time_keyboard=True)
