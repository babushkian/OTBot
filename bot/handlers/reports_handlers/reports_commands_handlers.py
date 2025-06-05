"""Обработчики команд для отчётов."""
from datetime import datetime, timedelta

from aiogram import Router, types
from aiogram.types import FSInputFile, BufferedInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.constants import tz
from bot.db.models import UserModel
from logger_config import log
from bot.common_utils import verify_string_as_integer
from bot.keyboards.common_keyboards import generate_cancel_button
from bot.repositories.violation_repo import ViolationRepository
from bot.handlers.reports_handlers.states import ReportStates
from bot.handlers.reports_handlers.reports_utils import validate_date_interval
from bot.handlers.reports_handlers.create_reports import create_typst_report, create_static_report
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.keyboards.inline_keyboards.callback_factories import ReportTypeFactory, ReportPeriodFactory

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
            log.debug("User {user} selected report type 'by_id'.", user=group_user.first_name)

        case "sum":
            periods_to_kb = (
                {"per": "today", "name": "Сегодня"},
                {"per": "month", "name": "С начала месяца"},
                {"per": "choose", "name": "Ввести интервал"},
            )
            periods_kb = await create_keyboard(items=periods_to_kb,
                                               text_key="name",
                                               callback_factory=ReportPeriodFactory)

            await callback.message.answer("Выберите период:", reply_markup=periods_kb)
            await state.set_state(ReportStates.sum)
            log.debug("User {user} selected report type 'sum'.", user=group_user.first_name)

        case "active":
            violation_repo = ViolationRepository(session)
            violations = await violation_repo.get_active_violations()
            result_report = create_typst_report(violations=violations,
                                                created_by=group_user)
            document = FSInputFile(result_report)
            await callback.message.bot.send_document(chat_id=callback.from_user.id,
                                                     document=document,
                                                     caption="Отчёт.")
            await callback.message.answer("Отчёт сгенерирован.")
            await state.clear()

            log.debug("User {user} selected report type 'active'.", user=group_user.first_name)

        case "review":
            violation_repo = ViolationRepository(session)
            violations = await violation_repo.get_not_reviewed_violations()
            result_report = create_typst_report(violations=violations,
                                                created_by=group_user)
            document = FSInputFile(result_report)
            await callback.message.bot.send_document(chat_id=callback.from_user.id,
                                                     document=document,
                                                     caption="Отчёт.")
            await callback.message.answer("Отчёт сгенерирован.")
            await state.clear()

            log.debug("User {user} selected report type 'review'.", user=group_user.first_name)

        case "stat":
            violation_repo = ViolationRepository(session)
            violations = await violation_repo.get_all_violations()

            report = create_static_report(violations=violations)
            document = BufferedInputFile(report, filename="static_report.xlsx")
            caption = "Итоговый расчёт за весь период."
            user_tg = callback.from_user.id
            await callback.bot.send_document(chat_id=user_tg, document=document, caption=caption)

            # await state.set_state(ReportStates.active)
            log.debug("User {user} selected report type 'stat'.", user=group_user.first_name)

    await callback.answer("Выбран тип отчёта.")


@router.message(ReportStates.by_id)
async def handle_report_by_id(message: types.Message, state: FSMContext,
                              group_user: UserModel,
                              session: AsyncSession) -> None:
    """Обработка ввода номера нарушения."""
    violation_id = message.text
    verified_input = verify_string_as_integer(violation_id)
    if not verified_input[0]:
        await message.answer(verified_input[1])
        return

    violation_repo = ViolationRepository(session)
    violation = await violation_repo.get_violation_by_id(int(violation_id))

    if violation is None:
        await message.answer("Не удалось найти отчёт по указанному номеру нарушения.")
        log.warning("Error finding file {violation_id} violation report file not exists.",
                    violation_id=violation_id)
        await state.clear()
        return

    try:
        pdf_file = create_typst_report(violations=(violation,), created_by=group_user)
        document = FSInputFile(pdf_file)
        caption = f"Нарушение №{violation_id}"
        await message.bot.send_document(chat_id=message.from_user.id,
                                        document=document,
                                        caption=caption)
        await state.clear()

    except Exception as e:
        log.error("Error sending violation {violation_id} report to user {group_user}.",
                  group_user=group_user.first_name,
                  violation_id=violation_id)
        log.exception(e)
    else:
        log.debug("Violation report №{violation_id} sent to user {group_user}.",
                  group_user=group_user.first_name,
                  violation_id=violation_id)


@router.callback_query(ReportStates.sum,
                       ReportPeriodFactory.filter())
async def handle_report_sum(callback: types.CallbackQuery,
                            state: FSMContext,
                            group_user: UserModel,
                            session: AsyncSession,
                            callback_data: ReportPeriodFactory) -> None:
    """Обработка ввода периода нарушения."""
    violation_repo = ViolationRepository(session)
    match callback_data.per:
        case "today":
            start_date = datetime.now(tz=tz) - timedelta(days=1)
            end_date = datetime.now(tz=tz)

            violations = await violation_repo.get_all_violations_by_date(start_date, end_date)

        case "month":
            start_date = datetime(day=1,
                                  month=datetime.now(tz=tz).month,
                                  year=datetime.now(tz=tz).year).astimezone(tz=tz)
            end_date = datetime.now(tz=tz)

            if start_date == end_date:
                start_date = datetime.now(tz=tz) - timedelta(days=1)

            violations = await violation_repo.get_all_violations_by_date(start_date, end_date)

        case "choose":
            await state.set_state(ReportStates.date_range)
            await callback.message.answer("Введите интервал дат в формате\n: день-месяц-год начальной даты"
                                          "[пробел]день-месяц-год конечной даты, например 01-01-2025 01-06-2025.\n"
                                          "Начальная дата должна быть раньше даты окончания.",
                                          )
            return

        case _:
            violations = None

    if not violations:
        log.warning("No data for report.")
        await callback.message.answer("Нет данных для отчёта.")
        await callback.answer("Нет данных для отчёта.")
        await state.clear()
        return

    try:
        result_report = create_typst_report(violations=violations,
                                            created_by=group_user)
        document = FSInputFile(result_report)
        await callback.message.bot.send_document(chat_id=callback.from_user.id,
                                                 document=document,
                                                 caption="Отчёт.")
        await callback.message.answer("Отчёт сгенерирован.")
        await callback.answer("Отчёт сгенерирован.")

    except Exception as e:
        log.error("Error generating report for user {group_user}.", group_user=group_user.first_name)
        log.exception(e)
    else:
        await state.clear()
        log.debug("User {user} selected report type 'sum'.",
                  user=group_user.first_name)
        log.debug("User {user} generated report successfully.",
                  user=group_user.first_name)


@router.message(ReportStates.date_range)
async def handle_report_range(message: types.Message,
                              group_user: UserModel,
                              session: AsyncSession,
                              state: FSMContext) -> None:
    """Обработчик ввода интервала дат."""
    dates = validate_date_interval(message.text)
    error_message = ("Неверный формат дат. "
                     "Пример формата: день-месяц-год начальной даты[пробел]день-месяц-год конечной даты, "
                     "например 01-01-2025 01-06-2025.\n"
                     "Начальная дата должна быть раньше даты окончания.\n"
                     "Число дней месяца и число не должны превышать максимальных значений."
                     "Введите снова или нажмите кнопку отмена.")
    if not dates:
        await message.answer(error_message)
        await state.set_state(ReportStates.date_range)
        return
    violation_repo = ViolationRepository(session)
    violations = await violation_repo.get_all_violations_by_date(dates[0], dates[1])
    if not violations:
        await message.answer("В выбранном периоде отчёт пуст.")
        return
    result_report = create_typst_report(violations=violations,
                                        created_by=group_user)
    document = FSInputFile(result_report)
    await message.bot.send_document(chat_id=message.from_user.id,
                                    document=document,
                                    caption="Отчёт.")
    await message.answer("Отчёт сгенерирован.")
    await state.clear()
