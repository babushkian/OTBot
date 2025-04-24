"""Базовые команды telegram."""
from aiogram import Router, types
from aiogram.filters import Command, CommandStart

router = Router(name=__name__)


@router.message(CommandStart())
async def handle_start(message: types.Message) -> None:
    """Команда старт."""
    start_text = """\nВас приветствует бот для регистрации нарушений ОТПБ.\n"""
    await message.answer(text=start_text)


@router.message(Command("help"))
async def handle_help(message: types.Message) -> None:
    """Инструкция приложения."""
    help_text = """\nИнструкция по использованию:\n"""

    await message.answer(text=help_text)
