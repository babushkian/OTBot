"""Перечисления приложения."""
from enum import StrEnum


class UserRole(StrEnum):
    """Роли пользователей."""

    OTPB = "РаботникООТПБиООС"
    RESPONSIBLE = "Ответственный"
    ADMIN = "РуководительООТПБиООС"
    USER = "Наблюдатель"


class ViolationStatus(StrEnum):
    """Статусы нарушений."""

    REVIEW = "проверяется"
    ACTIVE = "активно"
    CORRECTED = "устранено"
    REJECTED = "отклонено"
