"""Утилиты для area_handlers."""
from typing import Any

from bot.db.models import AreaModel


def get_fields_with_translations(line_id: int) -> list[dict[str, Any]]:
    """Получение списка имён полей модели с переводами."""
    return [
        {
            "field_name": column.name,
            "translation": column.info.get("verbose_name", column.name),
            "id": line_id,
        }
        for column in AreaModel.__table__.columns if column.name not in ("updated_at", "created_at", "id")
    ]
