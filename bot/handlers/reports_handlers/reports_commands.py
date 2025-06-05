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
        {"type": "sum", "name": "Полный отчёт нарушений за период"},
        {"type": "active", "name": "Действующие нарушения"},
        {"type": "review", "name": "На проверке"},
        {"type": "stat", "name": "Статистика нарушений"},
    )
    reports_kb = await create_keyboard(items=reports_to_kb,
                                       text_key="name",
                                       callback_factory=ReportTypeFactory)

    await message.answer("Выберите тип отчёта:", reply_markup=reports_kb)
