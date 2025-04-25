"""Базовые команды telegram."""
from aiogram import Router, types
from aiogram.filters import Command, CommandStart

from bot.db.models import UserModel
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

    await message.answer(
        "Для прохождения регистрации, пожалуйста, поделитесь своим контактом:",
        reply_markup=generate_share_contact_keyboard(),
    )


@router.message(Command("help"))
async def command_help(message: types.Message, user: UserModel | None) -> None:
    """Инструкция приложения."""
    help_text = ("""\nИнструкция по использованию: ДОБАВИТЬ ИНФОРМАЦИЮ\n"""
                 if user
                 else
                 """Для начала работы с ботом необходима регистрация. Для этого, введите команду /start.\n""")

    await message.answer(text=help_text)
