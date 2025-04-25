"""Общие обработчики."""
from aiogram import Router, types

from logger_config import log

router = Router(name=__name__)


@router.message(lambda message: message.text == "❌ Отмена")
async def handle_cancel_share_contact(message: types.Message) -> None:
    """Обрабатывает нажатие кнопки 'Отмена' при запросе контакта."""
    log.info("User {user} canceled sharing contact", user=message.from_user.id)
    await message.answer(
        "Без передачи контакта зарегистрироваться невозможно.",
        reply_markup=types.ReplyKeyboardRemove(),
    )
