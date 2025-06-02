"""Обработчики команд для отчётов."""
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.violation_repo import ViolationRepository
from bot.handlers.reports_handlers.create_reports import create_report

if TYPE_CHECKING:
    from pathlib import Path

from aiogram import Router, types
from aiogram.types import FSInputFile, BufferedInputFile
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
                                    session: AsyncSession,
                                    ) -> None:
    """Обработка выбора типа отчёта."""
    match callback_data.type:
        case "by_id":
            await callback.message.answer("Введите номер нарушения:", reply_markup=generate_cancel_button())
            await state.set_state(ReportStates.by_id)
            log.debug(f"User {group_user.first_name} selected report type 'by_id'.")

        case "sum":
            # отправка суммарного отчёта
            try:
                violation_repo = ViolationRepository(session)
                violations = await violation_repo.get_all_violations()
                result_report = create_report(violations)
                photo_file = BufferedInputFile(result_report, filename="report.xlsx")
                user_tg = callback.from_user.id
                await callback.message.bot.send_document(chat_id=user_tg,
                                                         document=photo_file,
                                                         caption="Отчёт.")
                await callback.message.answer("Отчёт сгенерирован.")
            except Exception as e:
                log.error("Error generating report for user {group_user}.", group_user=group_user.first_name)
                log.exception(e)
            else:
                log.debug("User {user} selected report type 'sum'.",
                          user=group_user.first_name)
                log.debug("User {user} generated report successfully.",
                          user=group_user.first_name)

        case "active":
            # TODO implementation
            # await state.set_state(ReportStates.active)
            log.debug(f"User {group_user.first_name} selected report type 'active'.")
            await callback.message.answer("Функционал пока не реализован.")

    await callback.answer("Выбран тип отчёта.")


@router.message(ReportStates.by_id)
async def handle_report_by_id(message: types.Message, state: FSMContext, group_user: UserModel) -> None:
    """Обработка ввода номера нарушения."""
    # TODO convert to pdf using Typst?
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
