
from pathlib import Path
from aiogram import F, Router, types
from aiogram.types import FSInputFile, BufferedInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import ViolationStatus
from bot.config import settings

from bot.db.models import UserModel
from bot.logger_config import log
from bot.keyboards.common_keyboards import  generate_yes_no_keyboard
from bot.repositories.violation_repo import ViolationRepository
from .states import ViolationCheckStates
from bot.handlers.reports_handlers.create_reports import create_typst_report
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.utils.image_utils import get_file
from bot.keyboards.inline_keyboards.callback_factories import (
    ViolationsFactory,
    ViolationsActionFactory,
)

router = Router(name=__name__)

@router.callback_query(ViolationsFactory.filter(), ViolationCheckStates.start)
async def handle_violation_review(
    callback: types.CallbackQuery,
    callback_data: ViolationsFactory,
    state: FSMContext,
    session: AsyncSession,
    group_user: UserModel,
) -> None:
    """Обработчик для просмотра нарушения при одобрении."""
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

    # отправка акта нарушения для review
    pdf_file = create_typst_report(violations=(violation,), created_by=group_user)
    caption = f"Место: {violation.area.name}\nОписание: {violation.description}"
    document = FSInputFile(pdf_file)
    user_tg = callback.from_user.id

    await callback.message.bot.send_document(chat_id=user_tg, document=document, caption=caption)

    actions_to_kb = ({"action": "activate", "name": "Утвердить"}, {"action": "reject", "name": "Отклонить"})
    action_kb = await create_keyboard(items=actions_to_kb, text_key="name", callback_factory=ViolationsActionFactory)

    await callback.message.answer("Выберите действие:", reply_markup=action_kb)
    await state.set_state(ViolationCheckStates.review)
    await callback.answer("Выбрано действие.")
    log.debug("Пользователь {user} запустил процесс рассмотрения нарушения {vn}({vi}). ",
              user=group_user.first_name,
              vn=violation.number,
              vi=violation.id
              )


@router.callback_query(ViolationsActionFactory.filter(F.action == "activate"), ViolationCheckStates.review)
async def handle_violation_activate(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обработчик для отправки уточнения при утверждении нарушения."""
    await callback.message.answer(
        "Вы уверены, что хотите УТВЕРДИТЬ данное нарушение?", reply_markup=generate_yes_no_keyboard()
    )
    await state.set_state(ViolationCheckStates.activate)
    await callback.answer("Выбрано действие утверждения.")


@router.message(ViolationCheckStates.activate, F.text.in_(["✅ Да", "❌ Нет"]))
async def handle_detection_activation_yes_no_response(
    message: types.Message, state: FSMContext, session: AsyncSession, group_user: UserModel
) -> None:
    """Обработчик для ответов "Да" или "Нет" при рассмотрении нарушения для одобрения."""
    data = await state.get_data()
    log.info("Последний этап допуска нарушения начальником.")
    log.info("Данные, содержащиеся в состоянии (про проверке): {d}", d=data)
    if message.text == "✅ Да":
        violation_repo = ViolationRepository(session)
        new_status = {"id": data["id"], "status": ViolationStatus.ACTIVE}

        success = await violation_repo.update_violation(violation_id=data["id"], update_data=new_status)
        violation_data = await violation_repo.get_violation_by_id(violation_id=data["id"])
        if success:
            # обратная связь зафиксировавшему нарушение
            await message.bot.send_message(
                chat_id=data["detector_tg"], text=f"Нарушение №{data['number']} одобрено администратором."
            )

            # отправка в группу
            image_path = settings.DATA_DIR / Path(violation_data.files[0].path)

            jpeg_file = get_file(image_path)

            caption_jpeg = f"Выявлено нарушение №{data['number']} в месте '{data['area']}'."
            caption_pdf = f"Детали нарушения №{data['number']}"
            log.info("файл, отправляемый в группу: {v.id}({v.number}) место: {v.area.name} описание: {v.description} ",
                     v=violation_data)
            pdf_file = create_typst_report(violations=(violation_data,), created_by=group_user)
            document = FSInputFile(pdf_file)

            try:
                await message.bot.send_document(
                    chat_id=settings.TG_GROUP_ID,
                    document=BufferedInputFile(
                        jpeg_file,
                        filename=f"Нарушение №{data['number']}.jpg"
                    ),
                    caption=caption_jpeg,
                )
                await message.bot.send_document(
                    chat_id=settings.TG_GROUP_ID,
                    document=document,
                    caption=caption_pdf)
                log.debug(
                    "Violation report {report}({number}) sent to group.", report=data["id"], number=data["number"]
                )
            except Exception as e:
                log.error("Error sending violation report to group.")
                log.exception(e)

            log.success(
                "Violation data {violation}({number}) updated to {new_status}",
                violation=data["id"],
                number=data["number"],
                new_status=ViolationStatus.ACTIVE.name,
            )
            await message.answer("Нарушение отправлено группу.")

        else:
            await message.answer("Возникла ошибка. Попробуйте позже.")
            log.error(
                "Error updating violation data {violation}({number})", violation=data["id"], number=data["number"]
            )

        await state.clear()

    elif message.text == "❌ Нет":
        await message.answer("Действие отменено, для повторного вызовите команду /check.")
        await state.clear()
        log.info("Violation data {user} update canceled", user=group_user.first_name)


@router.callback_query(ViolationsActionFactory.filter(F.action == "reject"), ViolationCheckStates.review)
async def handle_violation_reject(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик для отправки уточнения при отклонении нарушения."""
    await callback.message.answer(
        "Вы уверены, что хотите ОТКЛОНИТЬ данное нарушение?\n", reply_markup=generate_yes_no_keyboard()
    )
    await state.set_state(ViolationCheckStates.reject)
    await callback.answer("Выбрано действие отклонения.")


@router.message(ViolationCheckStates.reject, F.text.in_(["✅ Да", "❌ Нет"]))
async def handle_detection_rejection_yes_no_response(
    message: types.Message, state: FSMContext, session: AsyncSession, group_user: UserModel
) -> None:
    """Обработчик для ответов "Да" или "Нет" при отклонении нарушения."""
    data = await state.get_data()
    if message.text == "✅ Да":
        violation_repo = ViolationRepository(session)
        new_status = {"id": data["id"], "status": ViolationStatus.REJECTED}

        success = await violation_repo.update_violation(violation_id=data["id"], update_data=new_status)
        if success:
            # обратная связь зафиксировавшему нарушение
            await message.bot.send_message(
                chat_id=data["detector_tg"], text=f"Нарушение №{data['number']} ОТКЛОНЕНО администратором."
            )
            log.success("Violation data id {violation}({number}) updated", violation=data["id"], number=data["number"])
        else:
            await message.answer("Возникла ошибка. Попробуйте позже.")
            log.error(
                "Error updating violation id {violation}({number}) data ", violation=data["id"], number=data["number"]
            )

        await state.clear()

    elif message.text == "❌ Нет":
        await message.answer("Действие отменено, для повторного вызовите команду /check.")
        await state.clear()
        log.info("Violation data {user} update canceled", user=group_user.first_name)
