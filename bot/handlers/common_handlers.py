"""Общие обработчики."""
from aiogram import Router, types
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from logger_config import log
from bot.keyboards.common_keyboards import CancelCallbackFactory

router = Router(name=__name__)


@router.message(lambda message: message.text == "❌ Отмена")
async def handle_cancel_message(message: types.Message, state: FSMContext) -> None:
    """Обработчик кнопки Отмена."""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("❌ Заполнение данных отменено.")
    else:
        await message.answer("❌ Действие отменено.")

    log.info("User {user} canceled action", user=message.from_user.id)


@router.callback_query(CancelCallbackFactory.filter())
async def handle_cancel_callback(callback: CallbackQuery,
                                 callback_data: CancelCallbackFactory,
                                 state: FSMContext) -> None:
    """Обработчик для inline кнопки "Отмена"."""
    action = callback_data.action

    if action == "cancel":
        current_state = await state.get_state()
        if current_state:
            await state.clear()
            await callback.message.answer("❌ Заполнение данных отменено.")
        else:
            await callback.message.answer("❌ Действие отменено.")

        await callback.message.edit_reply_markup(reply_markup=None)

    await callback.answer("Действие отменено. Клавиатура удалена.")
    log.info("User {user} canceled action", user=callback.message.from_user.id)


