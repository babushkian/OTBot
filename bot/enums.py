"""Перечисления приложения."""
from enum import StrEnum


class UserRole(StrEnum):
    """Роли пользователей."""

    ADMIN = "admin"
    USER = "user"
    OTPB = "otpb"
    RESPONSIBLE = "responsible"


class ViolationCategory(StrEnum):
    """Категории нарушений."""

    CATEGORY_1 = "Категория 1"
    CATEGORY_2 = "Категория 2"
    CATEGORY_3 = "Категория 3"


class ViolationStatus(StrEnum):
    """Статусы нарушений."""

    ACTIVE = "активно"
    CORRECTED = "устранено"
