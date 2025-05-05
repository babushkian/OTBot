"""Обработчики обнаружения нарушений."""

from aiogram import F, Router, types
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import UserRole, ViolationStatus, ViolationCategory
from bot.constants import ACTIONS_NEEDED
from bot.db.models import UserModel, ViolationModel
from logger_config import log
from bot.reports.create_reports import create_pdf
from bot.repositories.area_repo import AreaRepository
from bot.repositories.user_repo import UserRepository
from bot.keyboards.common_keyboards import generate_cancel_button, generate_yes_no_keyboard
from bot.repositories.violation_repo import ViolationRepository
from bot.handlers.detection_handlers.states import DetectionStates, ViolationStates
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard, create_multi_select_keyboard
from bot.keyboards.inline_keyboards.callback_factories import (
    AreaSelectFactory,
    ViolationsFactory,
    ViolationsActionFactory,
    ViolationCategoryFactory,
    MultiSelectCallbackFactory,
)
from bot.handlers.detection_handlers.detection_keyboards import violation_categories_kb

router = Router(name=__name__)


@router.message(DetectionStates.send_photo)
async def get_violation_photo(message: types.Message,
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
async def set_violation_area(callback: types.CallbackQuery,
                             state: FSMContext,
                             callback_data: AreaSelectFactory,
                             group_user: UserModel,
                             ) -> None:
    """Обрабатывает заполнение места нарушения."""
    await state.update_data(area_id=callback_data.id)

    await callback.message.answer("Выберите категорию нарушения:",
                                  reply_markup=await violation_categories_kb())
    await callback.answer("Выбрано место нарушения.")

    await state.set_state(DetectionStates.select_category)
    log.debug(f"User {group_user.first_name} choose violation area.")


@router.callback_query(ViolationCategoryFactory.filter(), DetectionStates.select_category)
async def set_violation_category(callback: types.CallbackQuery,
                                 state: FSMContext,
                                 callback_data: ViolationCategoryFactory,
                                 group_user: UserModel,
                                 ) -> None:
    """Обрабатывает заполнение места нарушения."""
    await state.update_data(category=callback_data.category)

    actions_to_kb = [{"id": index, "text": action[:200]} for index, action
                     in enumerate(ACTIONS_NEEDED, start=1)]

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
async def handle_ok(callback: types.CallbackQuery,
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
    data_text = (f"\nМесто нарушения: {area.name}\n"
                 f"Описание: {data['description']}\n"
                 f"Категория: {ViolationCategory[data['category']]}\n"
                 f"Требуемые мероприятия: {', '.join(ACTIONS_NEEDED[index - 1][:100]
                                                     for index in data['actions_needed'])}")

    await callback.message.answer("Ввод данных завершен.\n"
                                  "Введённые данные:\n"
                                  f"{data_text}.\n\n"
                                  f"Всё верно?\n", reply_markup=generate_yes_no_keyboard())
    await state.set_state(DetectionStates.completed)


@router.message(DetectionStates.completed, F.text.in_(["✅ Да", "❌ Нет"]))
async def handle_yes_no_response(message: types.Message, state: FSMContext,
                                 session: AsyncSession,
                                 group_user: UserModel) -> None:
    """Обработчик для ответов "Да" или "Нет" при одобрении пользователя."""
    data = await state.get_data()
    if message.text == "✅ Да":
        violation_repo = ViolationRepository(session)
        violation = ViolationModel(area_id=data["area_id"],
                                   description=data["description"],
                                   detector_id=data["detector_id"],
                                   category=data["category"],
                                   status=data["status"],
                                   picture=data["picture"],
                                   actions_needed=", ".join(ACTIONS_NEEDED[index - 1]
                                                            for index in data["actions_needed"]),
                                   )
        success = await violation_repo.add_violation(violation)
        if success:
            await message.answer(f"Данные нарушения {data["description"]} обновлены.")
            log.success("Violation data {violation} added", violation=data["description"])
            # оповещаем админов
            user_repo = UserRepository(session)
            admins = await user_repo.get_users_by_role(UserRole.ADMIN)
            admins_telegrams = [admin["telegram_id"] for admin in admins]
            for admin_id in admins_telegrams:
                await message.bot.send_message(admin_id,
                                               text=f"Новое нарушение: {data['description']}.\n"
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
    """Обработчик для просмотра нарушения."""
    await state.update_data(id=callback_data.id)
    violation_repo = ViolationRepository(session)
    violation = await violation_repo.get_violation_by_id(callback_data.id)

    pdf_file = BufferedInputFile(create_pdf(data=violation, image_scale=0.4), filename="violation.pdf")
    user_tg = callback.from_user.id
    caption = f"Нарушение с описанием: {violation['description']}"
    await callback.message.bot.send_document(chat_id=user_tg, document=pdf_file, caption=caption)

    actions_to_kb = ({"action": "activate", "name": "Утвердить"},
                     {"action": "delete", "name": "Удалить"})
    action_kb = await create_keyboard(items=actions_to_kb,
                                      text_key="name",
                                      callback_factory=ViolationsActionFactory)

    await callback.message.answer("Выберите действие:", reply_markup=action_kb)
    await state.set_state(ViolationStates.review)
    await callback.answer("Выбрано действие.")
    log.debug("Пользователь {user} запустил процесс рассмотрения замечания.", user=group_user.first_name)

# @router.callback_query(ViolationsActionFactory.filter(F.action == "activate"), ViolationStates.review)
# async def handle_violation_activate(callback: types.CallbackQuery,
#                                     callback_data: ViolationsActionFactory,
#                                     state: FSMContext,
#                                     session: AsyncSession,
#                                     group_user: UserModel) -> None:
#     """Обработчик для утверждения нарушения."""
#     await callback.message.answer("Вы уверены, что хотите утвердить данное нарушение?",
#                                   reply_markup=generate_yes_no_keyboard())
#     await state.set_state(ViolationStates.activate)
#     await callback.answer("Выбрано действие утверждения.")


# @router.callback_query(ViolationsActionFactory.filter(F.action == "delete"), ViolationStates.review)
# async def handle_violation_delete(callback: types.CallbackQuery,
#                                   callback_data: ViolationsActionFactory,
#                                   state: FSMContext,
#                                   session: AsyncSession,
#                                   group_user: UserModel
#                                   ) -> None:
#     """Обработчик для удаления нарушения."""
#     await callback.message.answer("Вы уверены, что хотите УДАЛИТЬ данное нарушение?\n"
#                                   "Нарушение будет безвозвратно удалено.",
#                                   reply_markup=generate_yes_no_keyboard())
#     await state.set_state(ViolationStates.delete)
#     await callback.answer("Выбрано действие удаления.")
