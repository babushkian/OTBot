"""Перечисления приложения."""
from enum import StrEnum


class UserRole(StrEnum):
    """Роли пользователей."""

    OTPB = "Работник ООТПБиООС"
    RESPONSIBLE = "Ответственный"
    #ADMIN = "Руководитель ООТПБиООС"
    ADMIN = "И.о. Руководителя ООТПБиООС"
    USER = "Наблюдатель"


class ViolationStatus(StrEnum):
    """Статусы нарушений."""

    REVIEW = "проверяется"
    ACTIVE = "активно"
    CORRECTED = "устранено"
    REJECTED = "отклонено"

class ImgOrientation(StrEnum):
    """Статусы нарушений."""

    VERT = "вертикальная"
    HORIZ = "горизонтальная"
