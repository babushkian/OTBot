"""Перечисления приложения."""
from enum import StrEnum


class UserRole(StrEnum):
    """Роли пользователей."""

    OTPB = "РаботникОТПБ"
    RESPONSIBLE = "Ответственный"
    ADMIN = "Администратор"
    USER = "Наблюдатель"


class ViolationCategory(StrEnum):
    """Категории нарушений."""

    CATEGORY_1 = "Категория 1"
    CATEGORY_2 = "Категория 2"
    CATEGORY_3 = "Категория 3"


class ViolationStatus(StrEnum):
    """Статусы нарушений."""

    REVIEW = "проверяется"
    ACTIVE = "активно"
    CORRECTED = "устранено"
    REJECTED = "отклонено"
