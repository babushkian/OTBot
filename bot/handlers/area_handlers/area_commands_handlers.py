"""Обработчики команд места нарушения."""
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import UserRole
from bot.db.models import AreaModel
from logger_config import log
from bot.common_utils import verify_string_as_filename
from bot.bot_exceptions import StringInputError
from bot.repositories.area_repo import AreaRepository
from bot.repositories.user_repo import UserRepository
from bot.keyboards.common_keyboards import generate_cancel_button, generate_yes_no_keyboard
from bot.handlers.area_handlers.states import AreaAddOrUpdateStates
from bot.handlers.area_handlers.area_handlers_utils import get_fields_with_translations
from bot.keyboards.inline_keyboards.create_keyboard import create_keyboard
from bot.keyboards.inline_keyboards.callback_factories import (
    AreaDeleteFactory,
    AreaSelectFactory,
    AreaFieldToUpdateFactory,
    ResponsibleForAreaFactory,
)

router = Router(name=__name__)


# TODO REFACTOR разнести логику добавления и обновления в разные файлы

@router.callback_query(AreaSelectFactory.filter(), AreaAddOrUpdateStates.start)
async def update_or_add_area(callback: types.CallbackQuery,
                             callback_data: AreaSelectFactory,
                             state: FSMContext) -> None:
    """Обрабатывает кнопку обновления или добавления места нарушения."""
    if callback_data.id == 0:
        await callback.message.answer("Введите название места нарушения:", reply_markup=generate_cancel_button())
        await state.set_state(AreaAddOrUpdateStates.enter_area_name)
        await callback.answer("Выбрано добавление нового места нарушения.")
        return

    areas_fields_to_kb = tuple(get_fields_with_translations(line_id=callback_data.id))
    fields_kb = await create_keyboard(items=areas_fields_to_kb, text_key="translation",
                                      callback_factory=AreaFieldToUpdateFactory)

    await callback.message.answer("Выберите поле для корректировки:", reply_markup=fields_kb)
    await callback.answer("Выбрано место нарушения для обновления данных.")


@router.callback_query(AreaFieldToUpdateFactory.filter(), AreaAddOrUpdateStates.start)
async def update_selected_area_field(callback: types.CallbackQuery,
                                     callback_data: AreaFieldToUpdateFactory,
                                     session: AsyncSession,
                                     state: FSMContext) -> None:
    """Обрабатывает кнопку выбранного поля для обновления данных места нарушения."""
    await state.update_data({"id": callback_data.id, "field_name": callback_data.field_name})
    if callback_data.field_name == "responsible_user_id":
        user_repo = UserRepository(session)
        responsible_users = await user_repo.get_users_by_role(UserRole.RESPONSIBLE)
        users_to_kb = [{"name": user["first_name"], "id": user["id"], "responsible_name": user["first_name"]}
                       for user in responsible_users]
        users_to_kb.append({"name": "Ввести вручную", "id": 0, "responsible_name": "Ввод вручную"})

        users_keyboard = await create_keyboard(items=tuple(users_to_kb),
                                               callback_factory=ResponsibleForAreaFactory,
                                               text_key="name")

        await callback.message.answer("Выберите ответственного", reply_markup=users_keyboard)
        await state.set_state(AreaAddOrUpdateStates.update_responsible)
        return

    await callback.message.answer("Введите новые значения:", reply_markup=generate_cancel_button())
    await callback.answer("Выбрано поле для обновления данных.")
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.set_state(AreaAddOrUpdateStates.update_field)


@router.callback_query(ResponsibleForAreaFactory.filter(), AreaAddOrUpdateStates.update_responsible)
async def update_area_responsible_user_id(callback: types.CallbackQuery,
                                          callback_data: ResponsibleForAreaFactory,
                                          state: FSMContext,
                                          session: AsyncSession) -> None:
    """Обновление текстового поля места нарушения."""
    value_to_update = callback_data.id
    data = await state.get_data()

    area_repo = AreaRepository(session)
    update_data = {data["field_name"]: value_to_update}
    await area_repo.update_area(area_id=data["id"], update_data=update_data)

    await callback.answer("Данные успешно обновлены.")
    await callback.message.edit_reply_markup(reply_markup=None)
    log.success("Responsible id user chosen updated successfully.")
    await state.clear()


@router.message(AreaAddOrUpdateStates.update_field)
async def update_any_area_field(message: types.Message,
                                state: FSMContext,
                                session: AsyncSession) -> None:
    """Обновление ответственного пользователя из зарегистрированных для места нарушения."""
    value_to_update = message.text
    data = await state.get_data()

    area_repo = AreaRepository(session)
    update_data = {data["field_name"]: value_to_update}
    await area_repo.update_area(area_id=data["id"], update_data=update_data)

    await message.answer("Данные успешно обновлены.")
    log.success("Responsible id user chosen updated successfully.")
    await state.clear()


@router.message(AreaAddOrUpdateStates.enter_area_name)
async def add_area_name(message: types.Message, state: FSMContext) -> None:
    """Обработка ввода имени места нарушения."""
    area_name = message.text
    await state.update_data(name=area_name)
    await state.set_state(AreaAddOrUpdateStates.enter_area_description)
    await message.answer("Введите описание места нарушения:", reply_markup=generate_cancel_button())


@router.message(AreaAddOrUpdateStates.enter_area_description)
async def add_area_description(message: types.Message,
                               state: FSMContext,
                               session: AsyncSession) -> None:
    """Обработка описания места нарушения."""
    area_description = message.text
    await state.update_data(description=area_description)
    await state.set_state(AreaAddOrUpdateStates.enter_responsible)
    user_repo = UserRepository(session)
    responsible_users = await user_repo.get_users_by_role(UserRole.RESPONSIBLE)
    users_to_kb = [{"name": user["first_name"], "id": user["id"], "responsible_name": user["first_name"]}
                   for user in responsible_users]
    users_to_kb.append({"name": "Ввести вручную", "id": 0, "responsible_name": "Ввод вручную"})

    users_keyboard = await create_keyboard(items=tuple(users_to_kb),
                                           callback_factory=ResponsibleForAreaFactory,
                                           text_key="name")

    await message.answer("Выберите ответственного", reply_markup=users_keyboard)


@router.callback_query(ResponsibleForAreaFactory.filter(), AreaAddOrUpdateStates.enter_responsible)
async def select_area_responsible_user(callback: types.CallbackQuery,
                                       callback_data: ResponsibleForAreaFactory,
                                       state: FSMContext) -> None:
    """Обрабатывает кнопку выбранного пользователя для одобрения."""
    if callback_data.id == 0:
        await callback.message.answer("Введите ФИО ответственного:", reply_markup=generate_cancel_button())
        await state.set_state(AreaAddOrUpdateStates.enter_responsible_text)
        await callback.answer()
        return

    await state.update_data(responsible_user_id=callback_data.id)
    data = await state.get_data()
    data_text = (f"\nМесто нарушения: {data['name']}\n"
                 f"Описание: {data['description']}\n"
                 f"Ответственный: {callback_data.responsible_name}\n")

    await callback.message.answer("Ввод данных завершен.\n"
                                  "Введённые данные:\n"
                                  f"{data_text}\n"
                                  f"Всё верно?", reply_markup=generate_yes_no_keyboard())
    await callback.answer("Выбран ответственный из списка.")
    log.success("Responsible id user chosen with name {responsible} saved in data state",
                responsible=callback_data.responsible_name)
    await state.set_state(AreaAddOrUpdateStates.completed)


@router.message(AreaAddOrUpdateStates.enter_responsible_text)
async def add_area_responsible(message: types.Message, state: FSMContext) -> None:
    """Ввод вручную ответственного."""
    try:
        responsible_text = verify_string_as_filename(message.text)
    except StringInputError as e:
        await message.answer(text=f"Неверно введены данные. \n{e.args[0]}.\n"
                                  f"Начать с начала? /area",
                             parse_mode="HTML")
        log.warning("Wrong input for user name: {text}, by user {message}",
                    message=message.from_user.id, text=message.text)
        await state.clear()
        return

    await state.update_data(responsible_text=responsible_text)
    data = await state.get_data()

    data_text = (f"\nМесто нарушения: {data['name']}\n"
                 f"Описание: {data['description']}\n"
                 f"Ответственный: {data['responsible_text']}\n")

    await message.answer("Ввод данных завершен.\n"
                         "Введённые данные:\n"
                         f"{data_text}\n"
                         f"Всё верно?", reply_markup=generate_yes_no_keyboard())

    await state.set_state(AreaAddOrUpdateStates.completed)


@router.message(AreaAddOrUpdateStates.completed, F.text.in_(["✅ Да", "❌ Нет"]))
async def handle_yes_no_response(message: types.Message, state: FSMContext,
                                 session: AsyncSession,
                                 ) -> None:
    """Обработчик для ответов "Да" или "Нет" при добавлении маста нарушения."""
    data = await state.get_data()
    if message.text == "✅ Да":
        responsible_text = data.get("responsible_text", None)
        responsible_user_id = data.get("responsible_user_id", None)
        area = AreaModel(
            name=data["name"],
            description=data["description"],
            responsible_text=responsible_text,
            responsible_user_id=responsible_user_id,
        )
        area_repo = AreaRepository(session)

        success = await area_repo.add_area(area)
        if success:
            await message.answer(f"Данные места нарушения {data["name"]} добавлены.")
            log.success("Area data {area} added", area=data["name"])
        else:
            await message.answer("Возникла ошибка. Попробуйте позже.")
            log.error("Error adding area data {araa}", araa=data["name"])

        await state.clear()

    elif message.text == "❌ Нет":
        await message.answer("Заполнение отменено, для повторного вызовите команду /area.")
        await state.clear()
        log.info("Area data {area} update canceled", area=data["name"])


@router.callback_query(AreaDeleteFactory.filter())
async def delete_area(callback: types.CallbackQuery,
                      callback_data: AreaDeleteFactory,
                      session: AsyncSession,
                      ) -> None:
    """Обрабатывает кнопку удаления места нарушения."""
    area_id = callback_data.id
    area_repo = AreaRepository(session)
    await area_repo.delete_area_by_id(area_id=area_id)

    await callback.answer("Место нарушения удалёно из базы данных.")
    await callback.message.answer("Место нарушения успешно удалёно из базы данных.")
    await callback.message.edit_reply_markup(reply_markup=None)
    log.success("User {user} deleted from database", user=area_id)


