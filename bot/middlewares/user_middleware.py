"""Middleware пользователя."""
from typing import Any
from collections.abc import Callable, Awaitable

from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject

from logger_config import log


# from utils.handlers_utils import user_auth


class AuthMiddleware(BaseMiddleware):
    """Проверка и аутентификация пользователя отправляющего сообщения."""

    async def __call__(self,
                       handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: types,
                       data: dict[str, Any]) -> Any:  # noqa ANN401
        """Вызов middleware."""
        if event.message:
            # разрешённые команды
            allowed_messages = ("/start", "/register", "/help")
            message: types.Message = event.message
            if message.text in allowed_messages:
                log.debug("Допустимое сообщение {message} от пользователя {user_id}.",
                          message=message.text,
                          user_id=message.from_user.id)
                return await handler(event, data)

            # user = await user_auth(message)

            # if user is False:
            #     return None
            # data["user"] = user
            # data["bot"] = event.bot
            # log.debug("Сообщение зарегистрированного пользователя {user_id}.",
            #           user_id=user.telegram_id)

            return await handler(event, data)

        return None
