"""Настройка команд в меню клиента приложения телеграм."""
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat

from bot.enums import UserRole
from bot.constants import SUPER_USERS_TG_ID, otpb_commands, admin_commands, common_commands
from bot.db.models import UserModel


async def set_bot_commands(bot: Bot, user: UserModel) -> None:
    """Установка команд в меню клиента приложения телеграм."""
    match user.user_role:
        case UserRole.ADMIN:
            commands = [
                BotCommand(**command) for command in admin_commands
            ]
        case UserRole.OTPB:
            commands = [
                BotCommand(**command) for command in otpb_commands
            ]
        case _:
            commands = [
                BotCommand(**command) for command in common_commands
            ]

    if user.telegram_id in SUPER_USERS_TG_ID:
        commands = [
            BotCommand(**command) for command in admin_commands
        ]

    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=user.telegram_id))
