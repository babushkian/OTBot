"""Обработчики команд для отчётов."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from aiogram import Router, types
from aiogram.types import FSInputFile
from aiogram.fsm.context import FSMContext

from bot.config import REPORTS_DIR
from bot.db.models import UserModel
from logger_config import log
from bot.common_utils import verify_string_as_integer
from bot.keyboards.common_keyboards import generate_cancel_button
from bot.handlers.reports_handlers.states import ReportStates
from bot.keyboards.inline_keyboards.callback_factories import ReportTypeFactory

router = Router(name=__name__)


@router.callback_query(ReportTypeFactory.filter())
async def handle_report_type_select(callback: types.CallbackQuery,
                                    callback_data: ReportTypeFactory,
                                    state: FSMContext,
                                    group_user: UserModel,
                                    ) -> None:
    """Обработка выбора типа отчёта."""
    match callback_data.type:
        case "by_id":
            await callback.message.answer("Введите номер нарушения:", reply_markup=generate_cancel_button())
            await state.set_state(ReportStates.by_id)
            log.debug(f"User {group_user.first_name} selected report type 'by_id'.")
        case "active":
            await state.set_state(ReportStates.active)

            log.debug(f"User {group_user.first_name} selected report type 'active'.")
        case "sum":
            await state.set_state(ReportStates.sum)

            log.debug(f"User {group_user.first_name} selected report type 'sum'.")

    await callback.answer("Выбран тип отчёта.")


@router.message(ReportStates.by_id)
async def handle_report_by_id(message: types.Message, state: FSMContext, group_user: UserModel) -> None:
    """Обработка ввода номера нарушения."""
    violation_id = message.text
    verified_input = verify_string_as_integer(violation_id)
    if not verified_input[0]:
        await message.answer(verified_input[1])
        return

    # pdf_file: Path = REPORTS_DIR / f"report_{violation_id}.pdf"
    xlsx_file: Path = REPORTS_DIR / f"report_{violation_id}.xlsx"
    caption = f"Нарушение №{violation_id}"
    try:
        # if pdf_file.is_file():
        if xlsx_file.is_file():
            # document = FSInputFile(pdf_file)
            document = FSInputFile(xlsx_file)
            await message.bot.send_document(chat_id=message.from_user.id,
                                            document=document,
                                            caption=caption)
            await state.clear()
        else:
            await message.answer("Не удалось найти отчёт по указанному номеру нарушения. Попробуйте ещё раз.")
            log.warning("Error finding file {violation_id} violation report file not exists.",
                        violation_id=violation_id)
    except Exception as e:
        log.error("Error sending violation {violation_id} report to user {group_user}.",
                  group_user=group_user.first_name,
                  violation_id=violation_id)
        log.exception(e)
    else:
        log.debug("Violation report №{violation_id} sent to user {group_user}.",
                  group_user=group_user.first_name,
                  violation_id=violation_id)

