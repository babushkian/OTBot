"""Команды обработки обнаружения нарушений."""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import UserRole
from logger_config import log
from bot.repositories.user_repo import UserModel
from bot.keyboards.common_keyboards import generate_cancel_button
from bot.repositories.violation_repo import ViolationRepository
from bot.handlers.detection_handlers.states import DetectionStates, ViolationStates
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.keyboards.inline_keyboards.callback_factories import ViolationsFactory

router = Router(name=__name__)


@router.message(Command("detect"))
async def detect_violation(message: types.Message, access_denied: bool,
                           group_user: UserModel | None,
                           state: FSMContext) -> None:
    """Запуск процесса обнаружения нарушений."""
    if access_denied and group_user.user_role != UserRole.OTPB:
        return

    await message.reply("Отправьте фото нарушения:", reply_markup=generate_cancel_button())
    await state.set_state(DetectionStates.send_photo)
    log.debug("detect violation process started by {user}", user=group_user.first_name)


@router.message(Command("check"))
async def check_violation(message: types.Message,
                          access_denied: bool,
                          group_user: UserModel,
                          session: AsyncSession,
                          state: FSMContext) -> None:
    """Проверка (обновление/удаление) нарушения."""
    if access_denied and group_user.user_role != UserRole.ADMIN:
        return

    violation_repo = ViolationRepository(session)
    violations = await violation_repo.get_not_reviewed_violations()

    if not violations:
        await message.reply("Нет нарушений для проверки.")
        return

    violations_to_kb = tuple([{"id": violation.id,
                               "btn_name": f"Нарушение №{violation.id}-{violation.area.name}"}
                              for violation in violations])

    violations_kb = await create_keyboard(items=violations_to_kb, text_key="btn_name",
                                          callback_factory=ViolationsFactory)
    await message.answer("Выберите нарушение для проверки:", reply_markup=violations_kb)
    await state.set_state(ViolationStates.start)

