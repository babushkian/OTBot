"""Middleware пользователя."""
from typing import TYPE_CHECKING, Any
from collections.abc import Callable, Awaitable

from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from logger_config import log
from bot.bot_exceptions import EmptyDatabaseSessionError
from bot.repositories.user_repo import UserRepository


class UserCheckMiddleware(BaseMiddleware):
    """Middleware проверки пользователя."""

    async def __call__(self,
                       handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: types,
                       data: dict[str, Any]) -> tuple:
        """Запускает проверку пользователя."""
        session: AsyncSession = data.get("session")

        if not session:
            msg = "Session not found in middleware data"
            raise EmptyDatabaseSessionError(msg)

        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(event.from_user.id)

        if not user:
            command = event.text.split()[0] if event.text else "media_send"
            if command in ["/start", "/help", "media_send", "❌ Отмена"]:
                log.debug("Unauthorized user {user} used allowed command {command}",
                          user=event.from_user.id, command=command)
            else:
                log.warning("Attempt to access unauthorized user with id {user} by command {command}",
                            user=event.from_user.id, command=command)

            data["user"] = False
            return await handler(event, data)

        data["user"] = user
        return await handler(event, data)
