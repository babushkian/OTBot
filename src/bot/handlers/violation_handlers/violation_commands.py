"""Команды управления нарушениями."""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import UserRole
from bot.db.models import UserModel
from bot.repositories.violation_repo import ViolationRepository
from bot.handlers.violation_handlers.states import ViolationCloseStates
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.keyboards.inline_keyboards.callback_factories import ViolationsFactory

router = Router(name=__name__)


@router.message(Command("vclose"))
async def violation_close(
    message: types.Message,
    access_denied: bool,
    group_user: UserModel | None,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Закрытие нарушений."""
    if access_denied and group_user.user_role not in (UserRole.OTPB, UserRole.ADMIN):
        return

    violation_repo = ViolationRepository(session)
    violations = await violation_repo.get_active_violations()

    if not violations:
        await message.answer("Нет активных нарушений.")

    violations_to_kb: list = []
    for violation in violations:
        btn_info = {"id": violation.id, "btn_name": f"Нарушение №{violation.number}-{violation.area.name}"}
        violations_to_kb.append(btn_info)

    violations_kb = await create_keyboard(
        items=violations_to_kb, text_key="btn_name", callback_factory=ViolationsFactory
    )
    await message.answer("Выберите нарушение для закрытия:", reply_markup=violations_kb)
    await state.set_state(ViolationCloseStates.start)
