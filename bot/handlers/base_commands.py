"""Базовые команды telegram."""

from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import UserModel
from logger_config import log
from bot.repositories.user_repo import UserRepository
from bot.keyboards.common_keyboards import generate_share_contact_keyboard

router = Router(name=__name__)


@router.message(CommandStart())
async def handle_start(message: types.Message, user: UserModel | None) -> None:
    """Команда старт."""
    start_text = """\nВас приветствует бот для регистрации нарушений ОТПБ.\n"""
    await message.answer(text=start_text)
    if user:
        await message.answer(f"Здравствуйте, {user.first_name}, вы уже зарегистрированы.")
        return

    await message.answer(
        "Для прохождения регистрации, пожалуйста, поделитесь своим контактом:",
        reply_markup=generate_share_contact_keyboard(),
    )


@router.message(lambda message: message.contact is not None)
async def handle_contact_and_add_user(message: types.Message, session: AsyncSession) -> None:
    """Добавление пользователя в БД."""
    if message.contact:
        user_phone = message.contact.phone_number
        await message.answer(
            f"Спасибо! Ваш номер телефона: {user_phone}",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    else:
        await message.answer("Не удалось получить ваш контакт.")
    # TODO добавить в БД пользователя

    user_repo = UserRepository(session)
    user = UserModel()

    await user_repo.add_user(user)


@router.message(lambda message: message.text == "❌ Отмена")
async def handle_cancel_share_contact(message: types.Message) -> None:
    """Обрабатывает нажатие кнопки 'Отмена' при запросе контакта."""
    log.info("User {user} canceled sharing contact", user=message.from_user.id)
    await message.answer(
        "Без передачи контакта зарегистрироваться невозможно.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@router.message(Command("help"))
async def handle_help(message: types.Message, user: UserModel | None) -> None:
    """Инструкция приложения."""
    help_text = ("""\nИнструкция по использованию: ДОБАВИТЬ ИНФОРМАЦИЮ\n"""
                 if user
                 else
                 """Для начала работы с ботом необходима регистрация. Для этого, введите команду /start.\n""")

    await message.answer(text=help_text)
