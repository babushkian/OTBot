"""Настройка команд в меню клиента приложения телеграм."""
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.exceptions import TelegramBadRequest

from bot.enums import UserRole
from bot.constants import SUPER_USERS_TG_ID, otpb_commands, admin_commands, common_commands
from bot.db.models import UserModel
from logger_config import log
from bot.db.database import async_session_factory
from bot.repositories.user_repo import UserRepository


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

    try:
        await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=user.telegram_id))
    except TelegramBadRequest:
        log.warning("Пользователь {user} ({id}) не состоит в группе", user=user.first_name, id=user.telegram_id )


async def check_main_menu_on_startup(bot: Bot) -> None :
    """Индивидуально формирует главное меню для всех активных пользователей."""
    async with async_session_factory() as session:
        repo = UserRepository(session)
        users = await repo.get_approved_users()
        for user in users:
            await set_bot_commands(bot, user)
