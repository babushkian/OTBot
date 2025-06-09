"""Базовые команды telegram."""

from aiogram import Router, types
from aiogram.types import FSInputFile
from aiogram.filters import Command, CommandStart

from bot.config import BASEDIR
from bot.constants import TG_GROUP_ID
from bot.db.models import UserModel
from logger_config import log
from bot.set_bot_commands import set_bot_commands
from bot.keyboards.common_keyboards import generate_share_contact_keyboard

router = Router(name=__name__)


@router.message(CommandStart())
async def command_start(message: types.Message, user: UserModel | None) -> None:
    """Команда старт."""
    if user:
        start_text = f"Здравствуйте, {user.first_name}. Вы уже зарегистрированы."
        await message.answer(start_text)
        return
    start_text = """\nВас приветствует бот для регистрации нарушений ОТПБ.\n"""
    await message.answer(text=start_text)
    log.debug("Пользователь {user} запустил бот.", user=message.from_user.first_name)

    await message.answer(
        "Для прохождения регистрации, пожалуйста, поделитесь своим контактом:",
        reply_markup=generate_share_contact_keyboard(),
    )


@router.message(Command("instruction"))
async def command_instruction(message: types.Message,
                              group_user: UserModel,
                              access_denied: bool) -> None:
    """Получение инструкции по использованию."""
    if access_denied:
        msg = (f"У вас нет доступа к этой команде. Проверьте свою регистрацию командой /start. "
               f"Убедитесь, что состоите в группе {TG_GROUP_ID}, иначе обратитесь к администратору бота.")
        await message.answer(msg)
        log.warning("Пользователь без доступа с tg_id {user_id} запросил инструкцию.",
                    user_id=message.from_user.id)
        return
    instruction_file = BASEDIR / "bot" / "docs" / "docs OTBot.pdf"
    caption = "Инструкция OTBot"
    await message.bot.send_document(chat_id=message.from_user.id,
                                    document=FSInputFile(instruction_file),
                                    caption=caption)
    log.debug("Пользователь {group_user} получил инструкцию по использованию.", group_user=group_user.first_name)


@router.message(Command("help"))
async def command_help(message: types.Message, user: UserModel | None) -> None:
    """Инструкция приложения."""
    if user:
        await set_bot_commands(message.bot, user)
        help_text = "Получить подробную инструкцию в формате pdf можно по команде:\n/instruction"
    else:
        help_text = "Для начала работы с ботом необходима регистрация. Для этого, введите команду /start."
    await message.answer(text=help_text)
