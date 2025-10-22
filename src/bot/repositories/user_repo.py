"""Репозитории пользователя."""
from typing import Any, NewType
from collections.abc import Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import UserRole
from bot.db.models import UserModel
from bot.logger_config import log

UserList = NewType("UserList", list[dict[str, Any]])

class UserRepository:
    """Репозиторий пользователя."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория пользователя."""
        self.session = session

    async def get_user_by_telegram_id(self, user_telegram_id: int) -> UserModel | None:
        """Получение пользователя по telegram_id."""
        try:
            result = await self.session.execute(select(UserModel).where(UserModel.telegram_id == user_telegram_id))
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting user with id {user_id}", user_id=user_telegram_id)
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting user with id {user_id}", user_id=user_telegram_id)
            log.exception(e)
            return None
        else:
            log.success("User with id {user_id} found successfully", user_id=user_telegram_id)
            return result.scalars().first()


    async def get_user_by_id(self, user_id: int) -> UserModel | None:
        """Получение пользователя по идентификатору в таблице пользователей.

        Например, для передачи фамилии ответственного через инлайн-клавиатуру.
        """
        try:
            result = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting user with id {user_id}", user_id=user_id)
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting user with id {user_id}", user_id=user_id)
            log.exception(e)
            return None
        else:
            log.success("User with id {user_id} found successfully", user_id=user_id)
            return result.scalars().first()


    async def get_approved_user_by_telegram_id(self, user_telegram_id: int) -> UserModel | None:
        """Получение одобренного (is_approved=True) пользователя по telegram_id."""
        try:
            result = await self.session.execute(
                select(UserModel).where(
                    UserModel.telegram_id == user_telegram_id,
                    UserModel.is_approved == bool(1), UserModel.is_active.is_(True)))
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting user with id {user_id}", user_id=user_telegram_id)
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting user with id {user_id}", user_id=user_telegram_id)
            log.exception(e)
            return None
        else:
            log.success("User with id {user_id} found successfully", user_id=user_telegram_id)
            return result.scalars().first()

    async def add_user(self, user: UserModel) -> UserModel | None:
        """Добавление пользователя."""
        try:
            self.session.add(user)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError adding user with id {user_id}", user_id=user.telegram_id)
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error adding user with id {user_id}", user_id=user.telegram_id)
            log.exception(e)
            return None
        else:
            log.success("User with id {user_id} added successfully", user_id=user.telegram_id)
            return user

    async def get_users_by_role(self, role: UserRole) -> UserList | None:
        """Получение всех пользователей с указанной ролью."""
        try:
            users = await self.session.execute(select(UserModel).where(UserModel.user_role == role))
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting users with role: {role}", user_id=role)
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting users with role: {role}", role=role)
            log.exception(e)
            return None
        else:
            log.success("Users with role {role} found successfully", role=role)

            return UserList([user.to_dict() for user in users.scalars().all()])

    async def get_not_approved_users(self) -> UserList | None:
        """Получение всех не одобренных пользователей."""
        try:
            stmt = select(UserModel).where(UserModel.is_approved.is_(False), UserModel.is_active.is_(True))
            result = await self.session.execute(stmt)
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting not approved users")
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting not approved users")
            log.exception(e)
            return None
        else:
            log.success("Not approved users found successfully")
            return UserList([user.to_dict() for user in result.scalars().all()])

    async def get_approved_users(self) -> Sequence[UserModel] | None:
        """Получение всех не одобренных пользователей."""
        try:
            result = await self.session.execute(select(UserModel).where(UserModel.is_approved == bool(1),
                                                                        UserModel.is_active.is_(True)))
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting approved users")
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting approved users")
            log.exception(e)
            return None
        else:
            log.success("Approved users found successfully")
            return result.scalars().all()

    async def update_user_by_id(self, user_id: int, update_data: dict[str, Any]) -> bool:
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
            log.error("SQLAlchemyError updating user with id {user_id}", user_id=user_id)
            log.exception(e)
            return False
        except Exception as e:
            log.error("Error updating user with id {user_id}", user_id=user_id)
            log.exception(e)
            return False
        else:
            log.success("User data with id {user_id} updated successfully: {update_data}",
                        user_id=user_id, update_data=update_data)
            return True

    async def delete_user_by_id(self, user_id: int) -> None:
        """Удаление данных пользователя по его user_id."""
        stmt = (
            delete(UserModel)
            .where(UserModel.id == user_id)
        )
        try:
            await self.session.execute(stmt)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError deleting user with id {user_id}", user_id=user_id)
            log.exception(e)
            return
        except Exception as e:
            log.error("Error deleting user with id {user_id}", user_id=user_id)
            log.exception(e)
            return
        else:
            log.success("User with id {user_id} deleted successfully", user_id=user_id)
