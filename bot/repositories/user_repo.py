"""Репозитории приложения."""
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import UserRole
from bot.db.models import UserModel


class UserRepository:
    """Репозиторий пользователя."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория пользователя."""
        self.session = session

    async def get_user_by_telegram_id(self, user_telegram_id: int) -> UserModel:
        """Получение пользователя по telegram_id."""
        result = await self.session.execute(select(UserModel).where(UserModel.telegram_id == user_telegram_id))
        return result.scalars().first()

    async def add_user(self, user: UserModel) -> UserModel:
        """Добавление пользователя по telegram_id."""
        self.session.add(user)
        await self.session.commit()
        return user

    async def get_users_by_role(self, role: UserRole) -> list[dict[str, Any]]:
        """Получение всех пользователей с указанной ролью."""
        users = await self.session.execute(select(UserModel).where(UserModel.user_role == role))
        return [user.to_dict() for user in users.scalars().all()]

    async def get_users_not_approved_users(self) -> list[dict[str, Any]]:
        """Получение всех не одобренных пользователей."""
        result = await self.session.execute(select(UserModel).where(UserModel.is_approved is False))
        return [user.to_dict() for user in result.scalars().all()]
