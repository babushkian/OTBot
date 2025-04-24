"""Репозитории приложения."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import UserModel


class UserRepository:
    """Репозиторий пользователя."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория пользователя."""
        self.session = session

    async def get_user_by_telegram_id(self, user_telegram_id: int) -> UserModel:
        """Получение пользователя по telegram_id."""
        result = await self.session.execute(select(UserModel).where(UserModel.id == user_telegram_id))
        return result.scalars().first()

    async def add_user(self, user: UserModel) -> UserModel:
        """Добавление пользователя по telegram_id."""
        self.session.add(user)
        await self.session.commit()
        return user
