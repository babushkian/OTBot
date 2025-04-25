# ruff: noqa
"""Команды одобрения пользователей администратором."""
from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import UserModel
from bot.repositories.user_repo import UserRepository

router = Router(name=__name__)


@router.message(Command("approve"))
async def approve_command(message: types.Message, access_denied: bool,
                          group_user: UserModel | None,
                          session: AsyncSession) -> None:
    """Одобрение пользователя администратором."""
    if access_denied:
        return

    # user_repo = UserRepository(session)
    # res = await user_repo.get_users_not_approved_users()
    # print(res)

    # await message.bot.get_chat_member(TG_GROUP_ID, user_telegram_id)
    # TODO:
    # получения списка пользователей, которых можно одобрить
    # inline клавиатура с кнопкой отмена
    # далее после выбора в callback хендлере
    # добавление статуса is_approved
    # заполнение роли
    # заполнение фио
