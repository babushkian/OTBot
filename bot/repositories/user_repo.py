"""Репозитории приложения."""
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import UserRole
from bot.db.models import UserModel
from logger_config import log


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

    async def get_not_approved_users(self) -> list[dict[str, Any]]:
        """Получение всех не одобренных пользователей."""
        result = await self.session.execute(select(UserModel).where(UserModel.is_approved == bool(0)))
        return [user.to_dict() for user in result.scalars().all()]

    async def get_approved_users(self) -> list[dict[str, Any]]:
        """Получение всех не одобренных пользователей."""
        result = await self.session.execute(select(UserModel).where(UserModel.is_approved == bool(1)))
        return [user.to_dict() for user in result.scalars().all()]

    async def update_user_by_id(self, user_id: int, update_data: dict[str, Any]) -> None:
        """Обновление данных пользователя по его user_id."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(**update_data)
        )
        try:
            await self.session.execute(stmt)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("Ошибка при обновлении пользователя с ID {user_id}", user_id=user_id)
            log.exception(e)
            return
        except Exception as e:
            log.error("Непредвиденная ошибка при обновлении пользователя с id {user_id}", user_id=user_id)
            log.exception(e)
            return
        else:
            log.success("Данные пользователя с id {user_id} успешно обновлены: {update_data}",
                        user_id=user_id, update_data=update_data)
