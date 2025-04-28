"""Клавиатуры для одобрения пользователей."""
from aiogram.types import InlineKeyboardMarkup

from bot.enums import UserRole
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.keyboards.inline_keyboards.callback_factories import UserRoleFactory, ApproveUserFactory


async def unapproved_doers_kb(users: tuple[dict]) -> InlineKeyboardMarkup:
    """Не одобренные пользователи."""
    return await create_keyboard(
        items=users,
        text_key="phone_number",
        callback_factory=ApproveUserFactory,
    )


async def user_roles_kb() -> InlineKeyboardMarkup:
    """Роли пользователей."""
    roles = tuple([{"role": line.name, "name": line.value} for line in UserRole])

    return await create_keyboard(
        items=roles,
        text_key="name",
        callback_factory=UserRoleFactory,
    )



