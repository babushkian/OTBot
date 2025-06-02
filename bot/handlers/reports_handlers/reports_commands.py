"""Команды отчётов."""
from aiogram import Router, types
from aiogram.filters import Command

from bot.enums import UserRole
from bot.db.models import UserModel
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.keyboards.inline_keyboards.callback_factories import ReportTypeFactory

router = Router(name=__name__)


@router.message(Command("report"))
async def report_request(message: types.Message, access_denied: bool,
                         group_user: UserModel | None,
                         ) -> None:
    """Получение отчётов."""
    if access_denied and group_user.user_role not in (UserRole.OTPB, UserRole.ADMIN):
        return

    reports_to_kb = (
        {"type": "by_id", "name": "По номеру нарушения"},
        {"type": "sum", "name": "Полный перечень нарушений"},
        {"type": "active", "name": "Действующие нарушения"},
    )
    reports_kb = await create_keyboard(items=reports_to_kb,
                                       text_key="name",
                                       callback_factory=ReportTypeFactory)

    await message.answer("Выберите тип отчёта:", reply_markup=reports_kb)


# @router.message(Command("tst"))
# async def tst_report_request(
#         message: types.Message,
#         access_denied: bool,
#         group_user: UserModel | None,
#         session: AsyncSession,
# ) -> None:
#     """Запуск процесса обнаружения нарушений."""
#     if access_denied and group_user.user_role != UserRole.OTPB:
#         return
#
#     await message.answer("Отчёт сгенерирован.")
#
#     violation_repo = ViolationRepository(session)
#     # violation = await violation_repo.get_violation_by_id(violation_id=1)
#     violations = await violation_repo.get_all_violations()
#     # create_xlsx((violation,))
#     create_report(violations)

# TODO
# Команда получения суммарного отчёта xlsx по дате с с разными статусами в разных листах и листом статистики
# Команда получения активных нарушений
# Команда закрытия нарушений
# REFACTORING
# tests

# Обновление статуса любого нарушения ?
# Обновление любого поля любого нарушения ?
