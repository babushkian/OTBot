"""Обработчики обнаружения нарушений."""

from aiogram import F, Router, types
from aiogram.types import FSInputFile, BufferedInputFile, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import UserRole, ViolationStatus
from bot.constants import TG_GROUP_ID, ACTIONS_NEEDED
from bot.db.models import UserModel, ViolationModel
from logger_config import log
from bot.repositories.area_repo import AreaRepository
from bot.repositories.user_repo import UserRepository
from bot.keyboards.common_keyboards import generate_cancel_button, generate_yes_no_keyboard
from bot.repositories.violation_repo import ViolationRepository
from bot.handlers.detection_handlers.states import DetectionStates, ViolationStates
from bot.handlers.reports_handlers.create_reports import create_typst_report
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard, create_multi_select_keyboard
from bot.keyboards.inline_keyboards.callback_factories import (
    AreaSelectFactory,
    ViolationsFactory,
    ViolationsActionFactory,
    ViolationCategoryFactory,
    MultiSelectCallbackFactory,
)
from bot.handlers.detection_handlers.detection_keyboards import (
    violation_categories_first_kb,
    get_violation_category_by_cell_id,
    create_violation_keyboard_by_cell_id,
)

router = Router(name=__name__)


# TODO разнести логику ввода и одобрения/отклонения нарушения по разным файлам


@router.message(DetectionStates.send_photo)
async def handle_get_violation_photo(message: types.Message,
                                     state: FSMContext,
                                     group_user: UserModel,
                                     session: AsyncSession) -> None:
    """Обрабатывает получение фото нарушения."""
    if not message.photo:
        await message.answer("Необходимо прикрепить фото нарушения.",
                             reply_markup=generate_cancel_button())
        return

    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    description = message.caption or "Без описания"
    picture = await message.bot.download_file(file.file_path)

    await state.update_data(picture=picture.read(),
                            description=description,
                            detector_id=group_user.id,
                            status=ViolationStatus.REVIEW)

    area_repo = AreaRepository(session)
    areas = await area_repo.get_all_areas()

    areas_to_kb = [{"area_name": area.name, "id": area.id} for area in areas] if areas else []

    areas_keyboard = await create_keyboard(items=tuple(areas_to_kb), text_key="area_name",
                                           callback_factory=AreaSelectFactory)

    await message.reply("Выберите место нарушения:", reply_markup=areas_keyboard)
    log.debug(f"User {group_user.first_name} sent photo for detection.")
    await state.set_state(DetectionStates.enter_area)


@router.callback_query(AreaSelectFactory.filter(), DetectionStates.enter_area)
async def handle_set_area_and_first_layer_violation_category(callback: types.CallbackQuery,
                                                             state: FSMContext,
                                                             callback_data: AreaSelectFactory,
                                                             group_user: UserModel,
                                                             ) -> None:
    """Обрабатывает выбор места нарушения и отдаёт выбор первого уровня категории нарушения."""
    await state.update_data(area_id=callback_data.id)

    first_violation_keyboard = await violation_categories_first_kb()

    await callback.message.answer("Выберите категорию нарушения:", reply_markup=first_violation_keyboard)

    await callback.answer("Выбрано место нарушения.")

    await state.set_state(DetectionStates.next_layer_select_category)

    log.debug(f"User {group_user.first_name} choose violation area.")


@router.callback_query(ViolationCategoryFactory.filter(), DetectionStates.next_layer_select_category)
async def handle_set_second_layer_violation_category(callback: types.CallbackQuery,
                                                     state: FSMContext,
                                                     callback_data: ViolationCategoryFactory,
                                                     group_user: UserModel,
                                                     ) -> None:
    """Обрабатывает выбор второго уровня вложенности места нарушения."""
    # получение содержания первого уровня категории
    next_layer_keyboard_key = callback_data.category
    next_violation_keyboard = await create_violation_keyboard_by_cell_id(cell_id=next_layer_keyboard_key)

    if next_violation_keyboard is not None:
        # следующий уровень клавиатуры
        await callback.message.answer("Выберите подкатегорию категорию нарушения:",
                                      reply_markup=next_violation_keyboard)
        await callback.answer("Выбран второй уровень категории нарушения.")
        await state.set_state(DetectionStates.next_layer_select_category)
    else:
        # если клавиатуры нет, то запускаем следующий шаг
        await handle_set_violation_category(callback, state, callback_data, group_user)


@router.callback_query(ViolationCategoryFactory.filter(), DetectionStates.select_category)
async def handle_set_violation_category(callback: types.CallbackQuery,
                                        state: FSMContext,
                                        callback_data: ViolationCategoryFactory,
                                        group_user: UserModel,
                                        ) -> None:
    """Обрабатывает заполнение категории нарушения."""
    category = await get_violation_category_by_cell_id(callback_data.category)
    await state.update_data(category=category)
    actions = [line["action"] for line in ACTIONS_NEEDED]
    actions_to_kb = [{"id": index, "text": action[:200]} for index, action
                     in enumerate(actions, start=1)]

    await callback.message.answer("Выберите мероприятия для устранения нарушения:",
                                  reply_markup=await create_multi_select_keyboard(items=actions_to_kb),
                                  )
    await callback.answer("Выбрана категория нарушения.")

    await state.set_state(DetectionStates.select_actions_needed)
    log.debug(f"User {group_user.first_name} choose violation category.")


@router.callback_query(MultiSelectCallbackFactory.filter(F.action == "select"))
async def handle_multi_select(callback: types.CallbackQuery, callback_data: MultiSelectCallbackFactory) -> None:
    """Обработчик для inline-клавиатуры с множественным выбором."""
    item_id = callback_data.id
    selected = callback_data.selected

    new_selected = not selected

    message = callback.message
    keyboard = message.reply_markup.inline_keyboard

    updated_keyboard = []
    for row in keyboard:
        updated_row = []
        for button in row:
            factory = MultiSelectCallbackFactory.unpack(button.callback_data)
            if factory.action == "select" and factory.id == item_id:
                button.text = f"{'✅' if new_selected else '❌'} {button.text.split(' ', 1)[1]}"
                button.callback_data = MultiSelectCallbackFactory(id=item_id,
                                                                  action="select",
                                                                  selected=new_selected).pack()
            updated_row.append(button)
        updated_keyboard.append(updated_row)

    await message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=updated_keyboard))

    await callback.answer(f"Выбран элемент {item_id}: {'Да' if new_selected else 'Нет'}")
    log.debug(f"User {callback.from_user.first_name} selected item {item_id}.")


@router.callback_query(MultiSelectCallbackFactory.filter(F.action == "ok"),
                       DetectionStates.select_actions_needed)
async def handle_ok_button(callback: types.CallbackQuery,
                           state: FSMContext,
                           session: AsyncSession) -> None:
    """Обработчик для кнопки "ОК" после выбора мероприятий для устранения нарушения."""
    keyboard = callback.message.reply_markup.inline_keyboard
    selected_ids = []
    for row in keyboard:
        for button in row:
            factory = MultiSelectCallbackFactory.unpack(button.callback_data)
            if factory.action == "select" and factory.selected:
                selected_ids.append(factory.id)

    await state.update_data(actions_needed=selected_ids)

    await callback.answer("Выбор завершен.")

    data = await state.get_data()

    area_repo = AreaRepository(session)
    area = await area_repo.get_area_by_id(data["area_id"])
    # Отправляем фото
    photo_file = BufferedInputFile(data["picture"], filename="photo.jpg")
    user_tg = callback.from_user.id
    caption = f"Вы отправили фото нарушения с описанием: {data['description']}"
    await callback.message.bot.send_photo(chat_id=user_tg, photo=photo_file, caption=caption)

    # текст для проверки
    # actions = [line["action"] for line in ACTIONS_NEEDED]
    actions = [f"{line["action"]}. Срок устранения: {line["fix_time"]}" for line in ACTIONS_NEEDED]
    data_text = (f"\nМесто нарушения: {area.name}\n"
                 f"Описание: {data['description']}\n"
                 f"Категория: {data['category']}\n"
                 f"Требуемые мероприятия: {',\n'.join(actions[index - 1][:100]
                                                      for index in data['actions_needed'])}")

    await callback.message.answer("Ввод данных завершен.\n\n"
                                  "Введённые данные:\n"
                                  f"{data_text}.\n\n"
                                  f"Всё верно?\n", reply_markup=generate_yes_no_keyboard())
    await state.set_state(DetectionStates.completed)


@router.message(DetectionStates.completed, F.text.in_(["✅ Да", "❌ Нет"]))
async def handle_detection_yes_no_response(message: types.Message, state: FSMContext,
                                           session: AsyncSession,
                                           group_user: UserModel) -> None:
    """Обработчик для ответов "Да" или "Нет" при обнаружении нарушения."""
    data = await state.get_data()
    if message.text == "✅ Да":
        # actions = [line["action"] for line in ACTIONS_NEEDED]
        actions = [f"{line["action"]}. Срок устранения: {line["fix_time"]}" for line in ACTIONS_NEEDED]
        violation_repo = ViolationRepository(session)
        violation = ViolationModel(area_id=data["area_id"],
                                   description=data["description"],
                                   detector_id=data["detector_id"],
                                   category=data["category"],
                                   status=data["status"],
                                   picture=data["picture"],
                                   actions_needed=",\n".join(actions[index - 1]
                                                             for index in data["actions_needed"]),
                                   )
        success = await violation_repo.add_violation(violation)
        if success:
            await message.answer(f"Данные нарушения №{success.id} сохранены.")
            log.success("Violation data {violation} added", violation=data["description"])
            # оповещаем админов
            user_repo = UserRepository(session)
            admins = await user_repo.get_users_by_role(UserRole.ADMIN)
            admins_telegrams = [admin["telegram_id"] for admin in admins]
            for admin_id in admins_telegrams:
                await message.bot.send_message(admin_id,
                                               text=f"Новое нарушение:\n"
                                                    f"Описание: '{data['description']}'.\n"
                                                    f"Зафиксировано {group_user.first_name}.\n"
                                                    f"Номер нарушения {success.id}.\n"
                                                    f"Для проверки используйте команду /check.")
            log.debug("Notification sent to {admins}", admins=admins_telegrams)
            await message.answer("Нарушение отправлено администраторам на одобрение.")
        else:
            await message.answer("Возникла ошибка. Попробуйте позже.")
            log.error("Error updating violation data {violation}", violation=data["description"])

        await state.clear()

    elif message.text == "❌ Нет":
        await message.answer("Заполнение отменено, для повторного вызовите команду /detect.")
        await state.clear()
        log.info("Violation data {user} update canceled", user=group_user.first_name)


@router.callback_query(ViolationsFactory.filter(), ViolationStates.start)
async def handle_violation_review(callback: types.CallbackQuery,
                                  callback_data: ViolationsFactory,
                                  state: FSMContext,
                                  session: AsyncSession,
                                  group_user: UserModel) -> None:
    """Обработчик для просмотра нарушения при одобрении."""
    await state.update_data(id=callback_data.id)
    violation_repo = ViolationRepository(session)
    violation = await violation_repo.get_violation_by_id(callback_data.id)
    await state.update_data(detector_tg=violation["detector"]["telegram_id"],
                            description=violation["description"],
                            area=violation["area"]["name"])

    # отправка акта нарушения для review
    pdf_file = create_typst_report(violations=(violation,), created_by=group_user)
    caption = f"Место: {violation['area']['name']}\nОписание: {violation['description']}"
    document = FSInputFile(pdf_file)
    user_tg = callback.from_user.id

    await callback.message.bot.send_document(chat_id=user_tg, document=document, caption=caption)

    actions_to_kb = ({"action": "activate", "name": "Утвердить"},
                     {"action": "reject", "name": "Отклонить"})
    action_kb = await create_keyboard(items=actions_to_kb,
                                      text_key="name",
                                      callback_factory=ViolationsActionFactory)

    await callback.message.answer("Выберите действие:", reply_markup=action_kb)
    await state.set_state(ViolationStates.review)
    await callback.answer("Выбрано действие.")
    log.debug("Пользователь {user} запустил процесс рассмотрения нарушения.", user=group_user.first_name)


@router.callback_query(ViolationsActionFactory.filter(F.action == "activate"), ViolationStates.review)
async def handle_violation_activate(callback: types.CallbackQuery,
                                    state: FSMContext) -> None:
    """Обработчик для отправки уточнения при утверждении нарушения."""
    await callback.message.answer("Вы уверены, что хотите УТВЕРДИТЬ данное нарушение?",
                                  reply_markup=generate_yes_no_keyboard())
    await state.set_state(ViolationStates.activate)
    await callback.answer("Выбрано действие утверждения.")


@router.message(ViolationStates.activate, F.text.in_(["✅ Да", "❌ Нет"]))
async def handle_detection_activation_yes_no_response(message: types.Message, state: FSMContext,
                                                      session: AsyncSession,
                                                      group_user: UserModel) -> None:
    """Обработчик для ответов "Да" или "Нет" при рассмотрении нарушения для одобрения."""
    data = await state.get_data()
    if message.text == "✅ Да":
        violation_repo = ViolationRepository(session)
        new_status = {"id": data["id"], "status": ViolationStatus.ACTIVE}

        success = await violation_repo.update_violation(violation_id=data["id"], update_data=new_status)
        violation_data = await violation_repo.get_violation_by_id(violation_id=data["id"])
        if success:
            # обратная связь зафиксировавшему нарушение
            await message.bot.send_message(chat_id=data["detector_tg"],
                                           text=f"Нарушение №{data["id"]} одобрено администратором.")

            # отправка в группу
            jpeg_file = violation_data["picture"]
            caption_jpeg = f"Выявлено нарушение №{data['id']} в месте '{data['area']}'."
            caption_pdf = f"Детали нарушения №{data['id']}"

            pdf_file = create_typst_report(violations=(violation_data,), created_by=group_user)
            document = FSInputFile(pdf_file)

            try:
                await message.bot.send_document(chat_id=TG_GROUP_ID,
                                                document=BufferedInputFile(jpeg_file,
                                                                           filename=f"Нарушение №{data['id']}.jpg"),
                                                caption=caption_jpeg)
                await message.bot.send_document(chat_id=TG_GROUP_ID,
                                                document=document,
                                                caption=caption_pdf)
                log.debug("Violation report {report} sent to group.", report=data["id"])
            except Exception as e:
                log.error("Error sending violation report to group.")
                log.exception(e)

            log.success("Violation data {violation} updated to {new_status}", violation=data["id"],
                        new_status=ViolationStatus.ACTIVE.name)
            await message.answer("Нарушение отправлено группу.")

        else:
            await message.answer("Возникла ошибка. Попробуйте позже.")
            log.error("Error updating violation data {violation}", violation=data["id"])

        await state.clear()

    elif message.text == "❌ Нет":
        await message.answer("Действие отменено, для повторного вызовите команду /check.")
        await state.clear()
        log.info("Violation data {user} update canceled", user=group_user.first_name)


@router.callback_query(ViolationsActionFactory.filter(F.action == "reject"), ViolationStates.review)
async def handle_violation_reject(callback: types.CallbackQuery,
                                  state: FSMContext,
                                  ) -> None:
    """Обработчик для отправки уточнения при отклонении нарушения."""
    await callback.message.answer("Вы уверены, что хотите ОТКЛОНИТЬ данное нарушение?\n",
                                  reply_markup=generate_yes_no_keyboard())
    await state.set_state(ViolationStates.reject)
    await callback.answer("Выбрано действие отклонения.")


@router.message(ViolationStates.reject, F.text.in_(["✅ Да", "❌ Нет"]))
async def handle_detection_rejection_yes_no_response(message: types.Message, state: FSMContext,
                                                     session: AsyncSession,
                                                     group_user: UserModel) -> None:
    """Обработчик для ответов "Да" или "Нет" при отклонении нарушения."""
    data = await state.get_data()
    if message.text == "✅ Да":
        violation_repo = ViolationRepository(session)
        new_status = {"id": data["id"], "status": ViolationStatus.REJECTED}

        success = await violation_repo.update_violation(violation_id=data["id"], update_data=new_status)
        if success:
            # обратная связь зафиксировавшему нарушение
            await message.bot.send_message(chat_id=data["detector_tg"],
                                           text=f"Нарушение №{data["id"]} ОТКЛОНЕНО администратором.")
            log.success("Violation data id {violation} updated", violation=data["id"])
        else:
            await message.answer("Возникла ошибка. Попробуйте позже.")
            log.error("Error updating violation id {violation} data ", violation=data["id"])

        await state.clear()

    elif message.text == "❌ Нет":
        await message.answer("Действие отменено, для повторного вызовите команду /check.")
        await state.clear()
        log.info("Violation data {user} update canceled", user=group_user.first_name)
