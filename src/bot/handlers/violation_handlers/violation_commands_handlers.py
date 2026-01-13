"""Обработчики команд управления нарушениями."""

from aiogram import F, Router, types
from aiogram.types import FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import ViolationStatus
from bot.config import settings
from bot.db.models import UserModel
from bot.logger_config import log
from bot.keyboards.common_keyboards import generate_yes_no_keyboard
from bot.repositories.violation_repo import ViolationRepository
from bot.handlers.violation_handlers.states import ViolationCloseStates
from bot.handlers.reports_handlers.create_reports import create_typst_report
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.keyboards.inline_keyboards.callback_factories import ViolationsFactory, ViolationsActionFactory

router = Router(name=__name__)


@router.callback_query(ViolationsFactory.filter(), ViolationCloseStates.start)
async def handle_violation_close(
    callback: types.CallbackQuery,
    callback_data: ViolationsFactory,
    state: FSMContext,
    session: AsyncSession,
    group_user: UserModel,
) -> None:
    """Обработчик для просмотра нарушения."""
    await callback.answer()
    await state.update_data(id=callback_data.id)
    violation_repo = ViolationRepository(session)
    violation = await violation_repo.get_violation_by_id(callback_data.id)
    if violation is None:
        log.error("Не существует нарушения с id={id}", id=callback_data.id)

    await state.update_data(
        number=violation.number,
        detector_tg=violation.detector.telegram_id,
        description=violation.description,
        area=violation.area.name,
    )

    # отправка акта нарушения для проверки перед закрытием
    pdf_file = create_typst_report(violations=(violation,), created_by=group_user)
    caption = f"Место: {violation.area.name}\nОписание: {violation.description}"
    document = FSInputFile(pdf_file)
    user_tg = callback.from_user.id

    await callback.message.bot.send_document(chat_id=user_tg, document=document, caption=caption)

    actions_to_kb = ({"action": "activate", "name": "Закрыть нарушение"},)
    action_kb = await create_keyboard(items=actions_to_kb, text_key="name", callback_factory=ViolationsActionFactory)

    await callback.message.answer("Выберите действие:", reply_markup=action_kb)
    await state.set_state(ViolationCloseStates.review)
    log.debug("Пользователь {user} запустил процесс закрытия нарушения.", user=group_user.first_name)


@router.callback_query(ViolationsActionFactory.filter(F.action == "activate"), ViolationCloseStates.review)
async def handle_violation_close_activation(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обработчик для отправки уточнения при утверждении нарушения."""
    await callback.message.answer(
        "Вы уверены, что хотите ЗАКРЫТЬ данное нарушение?", reply_markup=generate_yes_no_keyboard()
    )
    await state.set_state(ViolationCloseStates.close)


@router.message(ViolationCloseStates.close, F.text.in_(["✅ Да", "❌ Нет"]))
async def handle_violation_close_yes_no_response(
    message: types.Message, state: FSMContext, session: AsyncSession, group_user: UserModel
) -> None:
    """Обработчик для ответов "Да" или "Нет" при рассмотрении нарушения для закрытия."""
    data = await state.get_data()
    if message.text == "✅ Да":
        violation_repo = ViolationRepository(session)
        new_status = {"id": data["id"], "status": ViolationStatus.CORRECTED}

        success = await violation_repo.update_violation(violation_id=data["id"], update_data=new_status)
        if success:
            # обратная связь зафиксировавшему нарушение и в группу
            succsess_message = f"Нарушение №{data['number']} закрыто."
            await message.bot.send_message(chat_id=data["detector_tg"], text=succsess_message)
            await message.bot.send_message(chat_id=settings.TG_GROUP_ID, text=succsess_message)

            log.success(
                "Violation data {violation}({number}) updated to {new_status}",
                violation=data["id"],
                number=data["number"],
                new_status=ViolationStatus.CORRECTED.name,
            )
            await message.answer("Сообщение о закрытии нарушения отправлено пользователю и в группу.")

        else:
            await message.answer("Возникла ошибка. Попробуйте позже.")
            log.error("Error updating violation data {violation}", violation=data["id"])

        await state.clear()

    elif message.text == "❌ Нет":
        await message.answer("Действие отменено, для повторения процесса вызовите команду /vclose.")
        await state.clear()
        log.info("Violation data {user} update canceled", user=group_user.first_name)
