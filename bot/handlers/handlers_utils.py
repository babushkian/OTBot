"""Утилиты для handlers."""
from typing import Any

from aiogram import types

from logger_config import log


async def get_telegram_data(message: types.Message) -> dict[str, Any]:
    """Получение данных о пользователе из телеграма."""
    try:
        raw_telegram_data = {str(data_key): str(val) for data_key, val in dict(message).items()}
    except Exception as e:
        raw_telegram_data = None
        log.debug("Error to convert telegram_data to json.")
        log.exception(e)

    return {"message_id": message.from_user.id,
            "date": message.date.strftime("%Y.%m.%d"),
            "user": {"username": message.from_user.username,
                     "first_name": message.from_user.first_name,
                     "full_name": message.from_user.full_name},
            "raw_telegram_data": raw_telegram_data,
            }
