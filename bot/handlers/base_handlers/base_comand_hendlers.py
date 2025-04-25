"""Обработчики базовых команд."""
from aiogram import Router, types
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import UserModel
from bot.repositories.user_repo import UserRepository
from bot.handlers.handlers_utils import get_telegram_data

router = Router(name=__name__)


@router.message(lambda message: message.contact is not None)
async def handle_contact_and_add_user(message: types.Message, session: AsyncSession) -> None:
    """Добавление пользователя в БД."""
    if message.contact:
        user_phone = message.contact.phone_number
        await message.answer(
            f"Спасибо. Вы успешно зарегистрировались с номером {user_phone}. "
            f"Ожидайте одобрения от администратора.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    else:
        await message.answer("Не удалось получить ваш контакт.")
        return

    user_repo = UserRepository(session)
    user = UserModel(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        phone_number=user_phone,
        telegram_data=await get_telegram_data(message),
    )
    await user_repo.add_user(user)
