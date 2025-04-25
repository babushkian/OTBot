"""Middleware получения соединения с БД."""
from typing import Any
from collections.abc import Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from logger_config import log


class DbSessionMiddleware(BaseMiddleware):
    """Middleware получения соединения с БД."""

    def __init__(self, session_pool: async_sessionmaker) -> None:
        """Инициализация middleware."""
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
    ) -> tuple:
        """Получение соединения с БД и добавление её в контекст."""
        log.info("Session created for.")
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)


