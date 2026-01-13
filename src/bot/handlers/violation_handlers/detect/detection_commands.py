"""Команды обработки обнаружения нарушений."""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.enums import UserRole
from bot.logger_config import log
from bot.repositories.user_repo import UserModel
from bot.keyboards.common_keyboards import generate_cancel_button
from .states import DetectionStates

router = Router(name=__name__)


@router.message(Command("detect"))
async def detect_violation(
    message: types.Message, access_denied: bool, group_user: UserModel | None, state: FSMContext
) -> None:
    """Запуск процесса обнаружения нарушений."""
    if access_denied and group_user.user_role != UserRole.OTPB:
        return

    await message.reply("Отправьте фото нарушения:", reply_markup=generate_cancel_button())
    await state.set_state(DetectionStates.send_photo)
    log.debug("detect violation process started by {user}", user=group_user.first_name)

