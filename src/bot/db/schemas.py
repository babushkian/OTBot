"""Модели pedantic для взаимодействия с базой данных."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from bot.enums import UserRole, ViolationStatus


class UserSchema(BaseModel):
    """Схема для взаимодействия с моделью пользователя."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    first_name: str | None
    last_name: str | None
    phone_number: str | None
    user_role: UserRole
    is_approved: bool
    is_active: bool
    telegram_data: dict | None
    user_description: str | None



class AreaSchema(BaseModel):
    """Схема для взаимодействия с моделью места нарушения."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    responsible_user_id: int | None
    responsible_text: str | None
    responsible_user: UserSchema | None  # вложено


class ViolationSchema(BaseModel):
    """Схема для взаимодействия с моделью нарушения."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    detector_id: int
    area_id: int
    description: str
    picture: bytes
    status: ViolationStatus
    category: str
    actions_needed: str
    created_at: datetime | None  # если у тебя есть это поле в модели
    area: AreaSchema
    detector: UserSchema
