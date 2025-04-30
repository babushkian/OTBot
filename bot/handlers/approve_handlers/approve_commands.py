"""Команды одобрения пользователей администратором."""
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import TG_GROUP_ID, SUPER_USERS_TG_ID
from bot.repositories.user_repo import UserRepository
from bot.handlers.approve_handlers.states import ApproveUserStates
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.keyboards.inline_keyboards.callback_factories import (
    ApproveUserFactory,
    DeletedUserFactory,
    DisApproveUserFactory,
)

router = Router(name=__name__)


# TODO добавить проверку на администратора group_user.role == UserRole.ADMIN для доступа пользователю администратору
@router.message(Command("approve"))
async def approve_command(message: types.Message,
                          session: AsyncSession,
                          state: FSMContext) -> None:
    """Одобрение пользователя администратором."""
    if message.from_user.id not in SUPER_USERS_TG_ID:
        return

    user_repo = UserRepository(session)
    users = await user_repo.get_not_approved_users()
    users_to_approve = tuple([{"id": line["id"], "phone_number": f"{line["first_name"]} {line["phone_number"]}"}
                              for line in users
                              if await message.bot.get_chat_member(TG_GROUP_ID, line["telegram_id"])])
    if not users_to_approve:
        await message.reply("Нет пользователей для одобрения.")
        return

    users_to_approve_kb = await create_keyboard(
        items=users_to_approve, text_key="phone_number", callback_factory=ApproveUserFactory,
    )

    await message.reply("Выберите пользователя для одобрения:", reply_markup=users_to_approve_kb)
    await state.set_state(ApproveUserStates.started)


# TODO добавить проверку на администратора group_user.role == UserRole.ADMIN для доступа пользователю администратору
@router.message(Command("disapprove"))
async def disapprove_command(message: types.Message, session: AsyncSession) -> None:
    """Одобрение пользователя администратором."""
    if message.from_user.id not in SUPER_USERS_TG_ID:
        return

    user_repo = UserRepository(session)
    users = await user_repo.get_approved_users()
    users_to_disapprove = tuple([{"id": line["id"], "phone_number": f"{line["first_name"]} {line["phone_number"]}"}
                                 for line in users
                                 if await message.bot.get_chat_member(TG_GROUP_ID, line["telegram_id"])])
    if not users_to_disapprove:
        await message.reply("Нет пользователей для отмены регистрации.")
        return

    users_to_approve_kb = await create_keyboard(
        items=users_to_disapprove, text_key="phone_number", callback_factory=DisApproveUserFactory,
    )

    await message.reply("Выберите пользователя для отмены одобрения:", reply_markup=users_to_approve_kb)


# TODO добавить проверку на администратора group_user.role == UserRole.ADMIN для доступа пользователю администратору
@router.message(Command("delapprove"))
async def delete_command(message: types.Message, session: AsyncSession) -> None:
    """Одобрение пользователя администратором."""
    if message.from_user.id not in SUPER_USERS_TG_ID:
        return

    user_repo = UserRepository(session)
    users = await user_repo.get_not_approved_users()
    users_to_delete = tuple([{"id": line["id"], "phone_number": f"{line["first_name"]} {line["phone_number"]}"}
                             for line in users
                             if await message.bot.get_chat_member(TG_GROUP_ID, line["telegram_id"])])
    if not users_to_delete:
        await message.reply("Нет пользователей для удаления. Перед удалением пользователя, "
                            "его регистрация должна быть отменена.")
        return

    users_to_delete_kb = await create_keyboard(
        items=users_to_delete, text_key="phone_number", callback_factory=DeletedUserFactory,
    )

    await message.reply("Выберите для отмены удаления:", reply_markup=users_to_delete_kb)
