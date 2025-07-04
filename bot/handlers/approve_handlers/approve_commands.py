"""Команды одобрения пользователей администратором."""
from typing import Any, NewType

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import UserRole
from bot.constants import TG_GROUP_ID, SUPER_USERS_TG_ID
from bot.db.models import UserModel
from logger_config import log
from bot.repositories.user_repo import UserRepository, UserList
from bot.handlers.approve_handlers.states import ApproveUserStates
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.keyboards.inline_keyboards.callback_factories import (
    ApproveUserFactory,
    DeletedUserFactory,
    DisApproveUserFactory,
)

router = Router(name=__name__)

async def check_chat_members(user_repo:UserRepository, users:UserList, message:types.Message) -> UserList:
    """Обработка случая, когда пользователь удалил бота и не может с ним взаимодействовать.

    Возможны два варианта:
    1) пользователь удалил бота до того, как его одобрили - тогда он удаляется.
    2) одобренный пользователь удалил бота - тогда он становится неактивным.
    """
    chat_members =  UserList([])
    for line in users:
        try:
            await message.bot.get_chat_member(TG_GROUP_ID, line["telegram_id"])
            chat_members.append(line)
        except TelegramBadRequest as e:
            log.error(e)
            if line["is_approved"]:
                log.info(f"Deactivating user {line["first_name"]}")
                await user_repo.update_user_by_id(line["id"], {"is_active": False})
            else:
                log.info(f"Deleting user {line["first_name"]}")
                # опасно сразу удалять пользователя, потому что на него могут ссылаться места и нарушения
                # поэтому пока просто предупреждаю
                # await user_repo.delete_user_by_id(user_id=line["id"])
    return chat_members


@router.message(Command("approve"))
async def approve_command(message: types.Message,
                          session: AsyncSession,
                          state: FSMContext,
                          group_user: UserModel) -> None:
    """Одобрение пользователя администратором."""
    if group_user.telegram_id not in SUPER_USERS_TG_ID:
        return
    no_users_message = "Нет пользователей для одобрения."
    user_repo = UserRepository(session)
    users = await user_repo.get_not_approved_users()
    if not users:
        await message.reply(no_users_message)
        return

    # проверено, что все юзеры доступны для бота
    cleaned_users = await check_chat_members(user_repo, users, message)
    if not cleaned_users:
        await message.reply(no_users_message)
        return

    users_to_approve = tuple([{"id": line["id"], "phone_number": f"{line["first_name"]} {line["phone_number"]}"}
                              for line in cleaned_users])
    users_to_approve_kb = await create_keyboard(
        items=users_to_approve, text_key="phone_number", callback_factory=ApproveUserFactory,
    )
    await message.reply("Выберите пользователя для одобрения:", reply_markup=users_to_approve_kb)
    await state.set_state(ApproveUserStates.started)


@router.message(Command("disapprove"))
async def disapprove_command(message: types.Message, session: AsyncSession, group_user: UserModel) -> None:
    """Одобрение пользователя администратором."""
    if group_user.user_role != UserRole.ADMIN:
        return
    no_users_message = "Нет пользователей для отмены регистрации."
    user_repo = UserRepository(session)
    users = await user_repo.get_approved_users()
    if not users:
        await message.reply(no_users_message)
        return
    cleaned_users = await check_chat_members(user_repo, users, message)
    if not cleaned_users:
        await message.reply(no_users_message)
        return
    users_to_disapprove = tuple([{"id": line["id"], "phone_number": f"{line["first_name"]} {line["phone_number"]}"}
                                 for line in cleaned_users])
    users_to_approve_kb = await create_keyboard(
        items=users_to_disapprove, text_key="phone_number", callback_factory=DisApproveUserFactory,
    )
    await message.reply("Выберите пользователя для отмены одобрения:", reply_markup=users_to_approve_kb)


@router.message(Command("delapprove"))
async def delete_command(message: types.Message,
                         session: AsyncSession,
                         group_user: UserModel) -> None:
    """Одобрение пользователя администратором."""
    # if message.from_user.id not in SUPER_USERS_TG_ID:
    #     return
    if group_user.user_role != UserRole.ADMIN:
        return

    user_repo = UserRepository(session)
    users = await user_repo.get_not_approved_users()
    no_users_message = ("Нет пользователей для удаления. \n"
                        "Перед удалением пользователя его регистрация должна быть отменена.")
    if not users:
        await message.reply(no_users_message)
        return
    cleaned_users = await check_chat_members(user_repo, users, message)
    if not cleaned_users:
        await message.reply(no_users_message)
        return
    users_to_delete = tuple([{"id": line["id"], "phone_number": f"{line["first_name"]} {line["phone_number"]}"}
                             for line in cleaned_users])
    users_to_delete_kb = await create_keyboard(
        items=users_to_delete, text_key="phone_number", callback_factory=DeletedUserFactory,
    )

    await message.reply("Выберите для отмены удаления:", reply_markup=users_to_delete_kb)
